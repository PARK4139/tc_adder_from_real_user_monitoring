"""Run family one-shot jobs in an authenticated, reusable native Windows console."""

import argparse
import json
import os
import queue
import secrets
import shutil
import subprocess
import sys
import threading
import time
import traceback
from multiprocessing.connection import Client, Listener
from pathlib import Path

import psutil
import win32api
import win32con
import win32console
import win32event
import win32gui
from filelock import FileLock
from win32com.shell import shell, shellcon

from cores.common.paths import D_ROOT, D_TEMP

D_CONSOLE = D_TEMP / "common" / "one_shot_console"
F_HOST = D_CONSOLE / "host.json"
F_SETTINGS = D_CONSOLE / "wrapper_settings.json"


def _save(path, data):
    candidate = path.with_suffix(".tmp")
    candidate.write_text(json.dumps(data), encoding="utf-8")
    candidate.replace(path)


def _live_host():
    if not F_HOST.exists():
        return None
    state = json.loads(F_HOST.read_text(encoding="utf-8"))
    try:
        process = psutil.Process(state["pid"])
        if (
            process.create_time() == state["create_time"]
            and win32gui.IsWindowVisible(state["hwnd"])
            and win32gui.GetClassName(state["hwnd"]) == "ConsoleWindowClass"
        ):
            return state
    except (psutil.NoSuchProcess, psutil.AccessDenied, win32gui.error):
        pass
    return None


def _request(host, message):
    with Client(tuple(host["address"]), authkey=bytes.fromhex(host["token"])) as client:
        client.send(message)
        return client.recv()


def _execute(uv, arguments):
    # Only this fixed project pipeline can be dispatched by this console host.
    process = subprocess.Popen(
        [
            uv,
            "run",
            "--locked",
            "python",
            "-m",
            "cores.hpe990.scripts.one_shot",
            "--uv",
            uv,
            *arguments,
        ],
        cwd=D_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = queue.SimpleQueue()

    def display():
        while (line := output.get()) is not None:
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()

    # A selected console must not suspend the actual worker or its exit result.
    threading.Thread(target=display, daemon=True).start()
    with (D_CONSOLE / f"worker-{process.pid}.log").open("wb") as log:
        for line in iter(process.stdout.readline, b""):
            log.write(line)
            log.flush()
            output.put(line)
    process.stdout.close()
    output.put(None)
    return process.wait()


def _host(token):
    hwnd = win32console.GetConsoleWindow()
    if not hwnd or win32gui.GetClassName(hwnd) != "ConsoleWindowClass":
        raise RuntimeError("A visible native ConsoleWindowClass is required")
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32console.SetConsoleTitle("auto_emulator one-shot")
    sys.stdin = open("CONIN$", "r", encoding="utf-8")
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout
    input_handle = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
    mode = input_handle.GetConsoleMode()
    input_handle.SetConsoleMode((mode | 0x0080) & ~0x0040)  # disable QuickEdit
    owned_pid = os.getpid()

    def cleanup(event):
        if event in (
            win32con.CTRL_CLOSE_EVENT,
            win32con.CTRL_LOGOFF_EVENT,
            win32con.CTRL_SHUTDOWN_EVENT,
        ):
            if F_HOST.exists() and json.loads(F_HOST.read_text())["pid"] == owned_pid:
                F_HOST.unlink(missing_ok=True)
        return False

    win32api.SetConsoleCtrlHandler(cleanup, True)
    with Listener(("127.0.0.1", 0), authkey=bytes.fromhex(token)) as listener:
        _save(
            F_HOST,
            {
                "pid": owned_pid,
                "create_time": psutil.Process().create_time(),
                "hwnd": hwnd,
                "address": listener.address,
                "token": token,
            },
        )
        # CMD uses the native console input/output, so the recycled host remains usable.
        with open("CONIN$", "r") as console_in, open("CONOUT$", "w") as console_out:
            prompt = subprocess.Popen(
                ["cmd.exe", "/k"],
                stdin=console_in,
                stdout=console_out,
                stderr=console_out,
                cwd=D_ROOT,
            )
        try:
            while True:
                with listener.accept() as client:
                    message = client.recv()
                    if message["action"] == "shutdown":
                        client.send(0)
                        return
                    if message["action"] != "run":
                        client.send(1)
                        continue
                    client.send(_execute(message["uv"], message["arguments"]))
        finally:
            # Clean only the exact prompt process owned by this console host.
            if prompt.poll() is None:
                prompt.terminate()
                prompt.wait(timeout=10)
            if F_HOST.exists() and json.loads(F_HOST.read_text())["pid"] == owned_pid:
                F_HOST.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--host-token")
    parser.add_argument("--no-terminal", action="store_true")
    parser.add_argument("--no-recycle", action="store_true")
    parser.add_argument("--close-console", action="store_true")
    args, remaining = parser.parse_known_args()
    D_CONSOLE.mkdir(parents=True, exist_ok=True)
    if args.host_token:
        try:
            _host(args.host_token)
        except BaseException:
            (D_CONSOLE / "host-failure.log").write_text(traceback.format_exc(), encoding="utf-8")
            raise
        return 0
    uv = shutil.which(args.uv) or args.uv
    if args.close_console:
        host = _live_host()
        return _request(host, {"action": "shutdown"}) if host else 0
    settings = (
        json.loads(F_SETTINGS.read_text())
        if F_SETTINGS.exists()
        else {"common/one_shot_show_terminal": True, "common/one_shot_recycle_terminal": True}
    )
    if args.no_terminal:
        settings["common/one_shot_show_terminal"] = False
    if args.no_recycle:
        settings["common/one_shot_recycle_terminal"] = False
    _save(F_SETTINGS, settings)
    with FileLock(str(D_CONSOLE / "host.lock"), timeout=30):
        host = _live_host()
        if not settings["common/one_shot_show_terminal"]:
            if host:
                _request(host, {"action": "shutdown"})
            return _execute(uv, remaining)
        hwnd = win32console.GetConsoleWindow()
        if (
            not host
            and hwnd
            and win32gui.IsWindowVisible(hwnd)
            and win32gui.GetClassName(hwnd) == "ConsoleWindowClass"
        ):
            return _execute(uv, remaining)
        if not host:
            token = secrets.token_hex(32)
            result = shell.ShellExecuteEx(
                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS | shellcon.SEE_MASK_FLAG_DDEWAIT,
                lpVerb="open",
                lpFile=str(Path(os.environ["SystemRoot"]) / "System32" / "conhost.exe"),
                lpParameters=subprocess.list2cmdline(
                    [
                        uv,
                        "run",
                        "--no-sync",
                        "python",
                        "-m",
                        "cores.common.scripts.one_shot_console",
                        "--host-token",
                        token,
                    ]
                ),
                lpDirectory=str(D_ROOT),
                nShow=win32con.SW_SHOWNORMAL,
            )
            deadline = time.monotonic() + 20
            handle = result["hProcess"]
            try:
                while not (host := _live_host()):
                    if (
                        win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_OBJECT_0
                        or time.monotonic() >= deadline
                    ):
                        raise RuntimeError("Native one-shot console failed to initialize")
                    time.sleep(0.1)
            finally:
                win32api.CloseHandle(handle)
    result = _request(host, {"action": "run", "uv": uv, "arguments": remaining})
    if not settings["common/one_shot_recycle_terminal"]:
        _request(host, {"action": "shutdown"})
    return result


if __name__ == "__main__":
    raise SystemExit(main())

"""Explorer-owned fixed-purpose helpers survive MCP SDK job-object cleanup."""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psutil
import pythoncom
import win32api
import win32con
import win32process
import win32security
from win32com.client import Dispatch
from win32com.shell import shell, shellcon

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import F_HPE990_SHORTCUT, hpe990_folders


def ram_executable() -> Path:
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "hpe990-ram.exe"
    else:
        path = hpe990_folders.D_HPE990_BUILD / "rust" / "release" / "hpe990-ram.exe"
    if not path.is_file():
        raise FileNotFoundError(f"Build Rust Real Activity Monitoring worker first: {path}")
    return path


def request_backend(kind: str, payload: dict) -> dict:
    if kind not in ("launch", "ram", "semantic_ram", "ui_viewer", "activity_log", "input"):
        raise ValueError("Unsupported backend operation")
    requests = hpe990_folders.D_HPE990_RUNTIME / "requests"
    requests.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    request = requests / f"{token}.json"
    response = requests / f"{token}.result.json"
    request.write_text(json.dumps({"kind": kind, **payload}), encoding="utf-8")
    if getattr(sys, "frozen", False):
        executable = sys.executable
        arguments = ["--backend", token]
    else:
        executable = str(Path(sys.executable).with_name("pythonw.exe"))
        arguments = ["-m", "cores.hpe990.functions.backend", token]
    pythoncom.CoInitialize()
    try:
        windows = Dispatch("Shell.Application").Windows()
        desktop = windows.FindWindowSW(0, 0, 8, 0, 1)
        if isinstance(desktop, tuple):
            desktop = desktop[0]
        desktop.Document.Application.ShellExecute(
            executable, subprocess.list2cmdline(arguments), str(D_ROOT), "open", 0
        )
        del desktop, windows
    finally:
        pythoncom.CoUninitialize()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if response.exists():
            result = json.loads(response.read_text(encoding="utf-8"))
            if "error" in result:
                raise RuntimeError(result["error"])
            return result
        time.sleep(0.05)
    raise TimeoutError(f"Explorer helper did not respond: {response}")


def run_backend(token: str) -> None:
    if len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
        raise ValueError("Invalid request token")
    requests = hpe990_folders.D_HPE990_RUNTIME / "requests"
    request = requests / f"{token}.json"
    response = requests / f"{token}.result.json"
    child = None
    try:
        data = json.loads(request.read_text(encoding="utf-8"))
        if data["kind"] == "launch":
            os.environ["QT_USE_NATIVE_WINDOWS"] = "1"
            pythoncom.CoInitialize()
            try:
                result = shell.ShellExecuteEx(
                    fMask=shellcon.SEE_MASK_NOCLOSEPROCESS | shellcon.SEE_MASK_FLAG_DDEWAIT,
                    lpVerb="open",
                    lpFile=str(F_HPE990_SHORTCUT),
                    nShow=win32con.SW_SHOWNORMAL,
                )
                handle = result["hProcess"]
                try:
                    pid = win32process.GetProcessId(handle)
                    process = psutil.Process(pid)
                    result = {
                        "pid": pid,
                        "create_time": process.create_time(),
                        "exe": process.exe(),
                        "backend_pid": os.getpid(),
                    }
                finally:
                    win32api.CloseHandle(handle)
            finally:
                pythoncom.CoUninitialize()
        elif data["kind"] == "ram":
            directory = Path(data["directory"]).resolve()
            directory.relative_to(hpe990_folders.D_HPE990_RUNTIME.resolve() / "ram")
            process = psutil.Process(data["pid"])
            if process.create_time() != data["create_time"]:
                raise ValueError("Stale process identity")
            with (directory / "worker-stderr.log").open("wb") as errors:
                child = subprocess.Popen(
                    [
                        str(ram_executable()),
                        str(process.pid),
                        data["session_id"],
                        str(directory),
                        str(data["interval_ms"]),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=errors,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                result = {
                    "pid": child.pid,
                    "create_time": psutil.Process(child.pid).create_time(),
                    "backend_pid": os.getpid(),
                }
                response.write_text(json.dumps(result), encoding="utf-8")
                child.wait()
                return
        elif data["kind"] == "semantic_ram":
            if getattr(sys, "frozen", False):
                raise RuntimeError(
                    "Semantic Real Activity Monitoring requires the updated source uv environment"
                )
            directory = Path(data["directory"]).resolve()
            directory.relative_to(hpe990_folders.D_HPE990_SEMANTIC_RAM.resolve())
            process = psutil.Process(data["pid"])
            if process.create_time() != data["create_time"]:
                raise ValueError("Stale process identity")
            with (directory / "worker-stderr.log").open("wb") as errors:
                child = subprocess.Popen(
                    [sys.executable, "-m", "cores.hpe990.functions.semantic_ram", str(directory)],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=errors,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                result = {
                    "pid": child.pid,
                    "create_time": psutil.Process(child.pid).create_time(),
                    "backend_pid": os.getpid(),
                }
                response.write_text(json.dumps(result), encoding="utf-8")
                child.wait()
                return
        elif data["kind"] == "input":
            request_path = Path(data["request"]).resolve()
            request_path.relative_to(hpe990_folders.D_HPE990_EVIDENCE.resolve())
            if request_path.suffix != ".json":
                raise ValueError("Input request must be a family evidence JSON")
            completed = subprocess.run(
                [str(hpe990_folders.F_HPE990_INPUT), str(request_path)],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            result = {"receipt": json.loads(completed.stdout)}
            # Read-only diagnostics; missing access is reported, never treated as proof of UIPI.
            request_data = json.loads(request_path.read_text(encoding="utf-8"))
            integrity = {}
            for role, pid in (("backend", os.getpid()), ("target", request_data.get("pid"))):
                if not pid:
                    continue
                try:
                    process_handle = win32api.OpenProcess(0x1000, False, pid)
                    try:
                        token_handle = win32security.OpenProcessToken(
                            process_handle, win32con.TOKEN_QUERY
                        )
                        try:
                            sid, _ = win32security.GetTokenInformation(
                                token_handle, win32security.TokenIntegrityLevel
                            )
                            integrity[role] = sid.GetSubAuthority(sid.GetSubAuthorityCount() - 1)
                        finally:
                            token_handle.Close()
                    finally:
                        process_handle.Close()
                except Exception as error:
                    integrity[role] = {"diagnostic_error": type(error).__name__}
            result["receipt"]["integrity_levels"] = integrity
        elif data["kind"] == "activity_log":
            from cores.hpe990.functions.activity_log import _directory

            directory = _directory(data["session_id"])
            with (directory / "worker-stderr.log").open("ab") as errors:
                child = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "cores.hpe990.functions.activity_log",
                        data["session_id"],
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=errors,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                result = {
                    "pid": child.pid,
                    "create_time": psutil.Process(child.pid).create_time(),
                    "backend_pid": os.getpid(),
                }
                response.write_text(json.dumps(result), encoding="utf-8")
                child.wait()
                return
        elif data["kind"] == "ui_viewer":
            from cores.hpe990.functions.ui_viewer import serve_viewer

            serve_viewer(token, data.get("session_id"), response)
            return
        else:
            raise ValueError("Unsupported operation")
    except Exception as error:
        result = {"error": f"{type(error).__name__}: {error}"}
    temporary = response.with_suffix(".pending")
    temporary.write_text(json.dumps(result), encoding="utf-8")
    temporary.replace(response)


if __name__ == "__main__":
    run_backend(sys.argv[1])

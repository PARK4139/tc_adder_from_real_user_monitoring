"""Manage the separately hosted, loopback-only HTTP MCP service."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import psutil

from cores.hpe990.common.paths import hpe990_folders

HOST = "127.0.0.1"
PORT = 8765
STATE_FILE = hpe990_folders.D_HPE990_RUNTIME / "mcp-http-server.json"


def _is_listening() -> bool:
    with socket.socket() as connection:
        connection.settimeout(0.2)
        return connection.connect_ex((HOST, PORT)) == 0


def _managed_process() -> psutil.Process | None:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        process = psutil.Process(int(data["pid"]))
        command = " ".join(process.cmdline()).lower()
        if process.is_running() and "--mcp-http" in command:
            return process
    except (OSError, ValueError, KeyError, psutil.Error, json.JSONDecodeError):
        pass
    return None


def _start() -> dict:
    if _is_listening():
        return {"status": "already_running", "url": f"http://{HOST}:{PORT}/mcp"}

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_path = hpe990_folders.D_HPE990_RUNTIME / "mcp-http-server.log"
    log = log_path.open("ab")
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--mcp-http"]
    else:
        command = [sys.executable, "-m", "cores.hpe990.mcp.server", "--mcp-http"]
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        child = subprocess.Popen(
            command,
            cwd=str(hpe990_folders.D_HPE990.parents[1]),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            close_fds=True,
        )
    finally:
        log.close()

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError(f"HTTP MCP server exited during startup; see {log_path}")
        if _is_listening():
            STATE_FILE.write_text(json.dumps({"pid": child.pid}), encoding="utf-8")
            return {"status": "started", "pid": child.pid, "url": f"http://{HOST}:{PORT}/mcp"}
        time.sleep(0.1)
    child.terminate()
    raise TimeoutError(f"HTTP MCP server did not listen within 10 seconds; see {log_path}")


def _kill() -> dict:
    process = _managed_process()
    if process is None:
        STATE_FILE.unlink(missing_ok=True)
        if _is_listening():
            return {"status": "running_unmanaged", "url": f"http://{HOST}:{PORT}/mcp"}
        return {"status": "stopped"}

    process.terminate()
    try:
        process.wait(timeout=10)
    except psutil.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    STATE_FILE.unlink(missing_ok=True)
    return {"status": "stopped", "pid": process.pid}


def mcp_server_manager(action: str) -> dict:
    """Start, kill, or restart the loopback HTTP MCP server managed by auto_emulator.

    The service is exposed at http://127.0.0.1:8765/mcp. It runs as a separate
    process so this MCP connection remains available while it is restarted.
    """
    if action not in {"kill", "start", "restart"}:
        raise ValueError("action must be one of: kill, start, restart")
    if action == "start":
        return _start()
    if action == "kill":
        return _kill()
    stopped = _kill()
    started = _start()
    return {"status": "restarted", "previous": stopped, "server": started}

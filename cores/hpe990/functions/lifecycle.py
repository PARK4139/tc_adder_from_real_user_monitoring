"""Fixed-target Windows lifecycle with shared, PID-reuse-safe session ownership."""

import json
import math
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psutil
import pythoncom
import win32con
import win32gui
import win32process
from filelock import FileLock
from win32com.client import Dispatch

from cores.hpe990.common.paths import (
    F_HPE990_EVENTS,
    F_HPE990_LOCK,
    F_HPE990_SESSION,
    F_HPE990_SHORTCUT,
    hpe990_folders,
)
from cores.hpe990.functions.startup import click_continue, continue_buttons


def log_event(event: str, **details) -> None:
    F_HPE990_EVENTS.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "adapter_pid": os.getpid(),
        **details,
    }
    # Separate short writes, serialized even across concurrent client adapters.
    with FileLock(str(F_HPE990_EVENTS) + ".lock", timeout=10):
        with F_HPE990_EVENTS.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _timeout(value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or not 0 < value <= 120:
        raise ValueError("timeout_seconds must be finite and between 0 and 120")
    return value


def _target() -> dict:
    if not F_HPE990_SHORTCUT.is_file():
        raise FileNotFoundError(f"Approved shortcut missing: {F_HPE990_SHORTCUT}")
    pythoncom.CoInitialize()
    try:
        shortcut = Dispatch("WScript.Shell").CreateShortcut(str(F_HPE990_SHORTCUT))
        target = Path(shortcut.TargetPath)
        result = {
            "shortcut": str(F_HPE990_SHORTCUT),
            "target": str(target),
            "arguments": shortcut.Arguments,
            "working_directory": shortcut.WorkingDirectory,
        }
        del shortcut
    finally:
        pythoncom.CoUninitialize()
    if not target.is_file() or target.name.lower() != "hpe_990pro.exe":
        raise ValueError("Shortcut must resolve to the installed hpe_990pro.exe")
    return result


def _process_record(process: psutil.Process) -> dict:
    return {"pid": process.pid, "create_time": process.create_time(), "exe": process.exe()}


def _alive(record: dict) -> bool:
    try:
        process = psutil.Process(record["pid"])
        return (
            process.is_running()
            and process.create_time() == record["create_time"]
            and os.path.normcase(process.exe()) == os.path.normcase(record["exe"])
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _target_processes(target: str) -> list[dict]:
    records = []
    for process in psutil.process_iter(["exe"]):
        try:
            if process.info["exe"] and os.path.normcase(process.info["exe"]) == os.path.normcase(
                target
            ):
                records.append(_process_record(process))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return records


def _windows(records: list[dict]) -> list[dict]:
    pids = {record["pid"] for record in records if _alive(record)}
    windows = []

    def collect(hwnd, _):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in pids and win32gui.IsWindowVisible(hwnd):
                windows.append(
                    {
                        "hwnd": hwnd,
                        "pid": pid,
                        "title": win32gui.GetWindowText(hwnd),
                        "class_name": win32gui.GetClassName(hwnd),
                        "rect": list(win32gui.GetWindowRect(hwnd)),
                    }
                )
        except win32gui.error:
            pass  # A window can disappear between enumeration and inspection.

    win32gui.EnumWindows(collect, None)
    return windows


def _read_session() -> dict | None:
    if not F_HPE990_SESSION.exists():
        return None
    return json.loads(F_HPE990_SESSION.read_text(encoding="utf-8"))


def _save_session(session: dict) -> None:
    hpe990_folders.D_HPE990_RUNTIME.mkdir(parents=True, exist_ok=True)
    candidate = F_HPE990_SESSION.with_suffix(".tmp")
    candidate.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    candidate.replace(F_HPE990_SESSION)


def _status(session: dict | None) -> dict:
    if session is None:
        return {
            "running": False,
            "ready": False,
            "session_id": None,
            "owned": False,
            "processes": [],
            "windows": [],
            "runtime_log": str(F_HPE990_EVENTS),
        }
    alive = [record for record in session["processes"] if _alive(record)]
    windows = _windows(alive)
    start_ready = any(window["title"] == "Edger" for window in windows)
    return {
        **session,
        "running": bool(alive),
        "ready": bool(alive and windows and (start_ready or session.get("startup_completed"))),
        "startup_completed": bool(alive and (start_ready or session.get("startup_completed"))),
        "processes": alive,
        "windows": windows,
        "runtime_log": str(F_HPE990_EVENTS),
    }


def emulator_status() -> dict:
    hpe990_folders.D_HPE990_RUNTIME.mkdir(parents=True, exist_ok=True)
    with FileLock(str(F_HPE990_LOCK), timeout=125):
        session = _read_session()
        status = _status(session)
        if not status["running"]:
            target = _target()
            records = _target_processes(target["target"])
            if records:
                session = {
                    **target,
                    "session_id": uuid.uuid4().hex,
                    "owned": False,
                    "processes": records,
                }
                _save_session(session)
                status = _status(session)
        log_event("status", session_id=status["session_id"], running=status["running"])
        return status


def launch_emulator(timeout_seconds: float = 30.0) -> dict:
    timeout_seconds = _timeout(timeout_seconds)
    hpe990_folders.D_HPE990_RUNTIME.mkdir(parents=True, exist_ok=True)
    with FileLock(str(F_HPE990_LOCK), timeout=125):
        target = _target()
        session = _read_session()
        current = _status(session)
        reused = current["running"]
        if not reused:
            existing = _target_processes(target["target"])
            session = {
                **target,
                "session_id": uuid.uuid4().hex,
                "owned": not bool(existing),
                "processes": existing,
            }
            if existing:
                reused = True
            else:
                from cores.hpe990.functions.backend import request_backend

                result = request_backend("launch", {})
                session["processes"] = [_process_record(psutil.Process(result["pid"]))]
                _save_session(session)
                log_event("launch_requested", **session)
        deadline = time.monotonic() + timeout_seconds
        from cores.hpe990.functions.monitoring import start_ram

        # Observe the startup dialog before sending Continue, and keep observing after return.
        if session["processes"]:
            start_ram(session["session_id"])
        continue_request = None
        while True:
            # Some installed launchers hand off to another process of the same target.
            known = {(p["pid"], p["create_time"]) for p in session["processes"]}
            for record in _target_processes(target["target"]):
                if (record["pid"], record["create_time"]) not in known:
                    session["processes"].append(record)
            _save_session(session)
            status = _status(session)
            buttons = continue_buttons(status["windows"])
            if len(buttons) > 1:
                raise RuntimeError("Ambiguous HPE990 Continue controls; refusing to click")
            if buttons and continue_request is None:
                from cores.hpe990.functions.ui import collect_ui

                session["startup_inventory"] = collect_ui(session["session_id"])["evidence"]
                from cores.hpe990.functions.monitoring import action_marker

                action_id = uuid.uuid4().hex
                action_marker(
                    session["session_id"],
                    action_id,
                    "requested",
                    {"action": "startup_continue", "hwnd": buttons[0]},
                )
                continue_request = click_continue(buttons[0])
                continue_request["action_id"] = action_id
                session["continue_action"] = continue_request
                _save_session(session)
                log_event(
                    "continue_requested", session_id=session["session_id"], **continue_request
                )
            if status["ready"]:
                if buttons:
                    # Do not report success while the startup dialog is still visible.
                    status["ready"] = False
                else:
                    session["startup_completed"] = True
                    _save_session(session)
                    status["startup_completed"] = True
                    status["reused"] = reused
                    from cores.hpe990.functions.ui import collect_ui

                    status["ready_inventory"] = collect_ui(session["session_id"])["evidence"]
                    if continue_request:
                        action_marker(
                            session["session_id"],
                            continue_request["action_id"],
                            "observed",
                            {"action": "startup_continue", "after": status["ready_inventory"]},
                        )
                    log_event("launch_ready", **status)
                    return status
            if time.monotonic() >= deadline:
                log_event("launch_timeout", **status)
                raise TimeoutError(
                    f"HPE990 did not reach its Edger screen after Continue within {timeout_seconds}s; "
                    f"session={session['session_id']}; log={F_HPE990_EVENTS}"
                )
            time.sleep(0.2)


def stop_session(session_id: str, force: bool = False, timeout_seconds: float = 15.0) -> dict:
    """Explicit, PID-reuse-safe application-only stop; force is never implicit."""
    if not force:
        return close_emulator(session_id, timeout_seconds)
    timeout_seconds = _timeout(timeout_seconds)
    with FileLock(str(F_HPE990_LOCK), timeout=125):
        session = _read_session()
        if not session or session["session_id"] != session_id:
            raise ValueError("Unknown or stale session_id")
        if not session["owned"]:
            raise PermissionError("Refusing to stop an externally started Emulator")
        from cores.hpe990.functions.monitoring import action_marker, start_ram

        alive = any(_alive(p) for p in session["processes"])
        action_id = uuid.uuid4().hex
        if alive:
            start_ram(session_id)
            action_marker(
                session_id,
                action_id,
                "requested",
                {"action": "session_stop", "exit_method": "explicit_force"},
            )
        targets = []
        for record in session["processes"]:
            if _alive(record):
                process = psutil.Process(record["pid"])
                process.terminate()
                targets.append(process)
        _, remaining = psutil.wait_procs(targets, timeout=timeout_seconds)
        result = _status(session)
        result.update(
            closed=not remaining and not result["running"],
            exit_method="explicit_force",
            action_id=action_id if alive else None,
        )
        log_event("session_stop_result", **result)
        return result


def close_emulator(session_id: str, timeout_seconds: float = 15.0) -> dict:
    timeout_seconds = _timeout(timeout_seconds)
    hpe990_folders.D_HPE990_RUNTIME.mkdir(parents=True, exist_ok=True)
    with FileLock(str(F_HPE990_LOCK), timeout=125):
        session = _read_session()
        if not session or session["session_id"] != session_id:
            raise ValueError("Unknown or stale session_id")
        if not session["owned"]:
            raise PermissionError("Refusing to close an externally started Emulator")
        status = _status(session)
        # Send only to the root windows; owned dialogs may require explicit interaction.
        from cores.hpe990.functions.ui import _native_tree

        roots = [
            w
            for w in _native_tree(session)
            if not w["parent"] and not w["owner"] and w["class_name"] == "QWidget"
        ]
        for window in roots:
            if not win32gui.GetWindow(window["hwnd"], win32con.GW_OWNER):
                win32gui.PostMessage(window["hwnd"], win32con.WM_CLOSE, 0, 0)
        deadline = time.monotonic() + timeout_seconds
        while True:
            status = _status(session)
            if not status["running"] or time.monotonic() >= deadline:
                status["closed"] = not status["running"]
                log_event("close_result", **status)
                return status
            time.sleep(0.2)

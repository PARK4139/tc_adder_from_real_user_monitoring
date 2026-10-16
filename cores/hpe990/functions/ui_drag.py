"""UI-ID-bound native drag with Rust pacing, live identity guards and Real Activity Monitoring evidence."""

import json
import math
import subprocess
import time
import uuid

import win32con
import win32gui
import win32process
from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.monitoring import action_marker, ram_status, session_guard, start_ram
from cores.hpe990.functions.ui import _native_tree, collect_ui, win32api_position


def validate_drag(start_fraction, end_fraction, duration_ms):
    for point in (start_fraction, end_fraction):
        if len(point) != 2 or any(
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or not math.isfinite(v)
            or not 0 < v < 1
            for v in point
        ):
            raise ValueError("Fractions must contain two finite values strictly between 0 and 1")
    if (
        isinstance(duration_ms, bool)
        or not isinstance(duration_ms, int)
        or not 50 <= duration_ms <= 5000
    ):
        raise ValueError("duration_ms must be an integer between 50 and 5000")


def resolve_drag_node(record, ui_id):
    matches = [node for node in record["nodes"] if node["ui_id"] == ui_id]
    if len(matches) != 1:
        raise ValueError("Drag requires one currently observed native UI ID")
    node = matches[0]
    by_handle = {n["hwnd"]: n for n in record["nodes"]}
    current, seen = node, set()
    while current["hwnd"] not in seen:
        seen.add(current["hwnd"])
        if not current["visible"] or not current["enabled"]:
            raise ValueError("Drag target or ancestor is hidden or disabled")
        if current["parent"] not in by_handle:
            break
        current = by_handle[current["parent"]]
    return node


def _point(node, fraction):
    left, top, right, bottom = win32gui.GetClientRect(node["hwnd"])
    if right <= left or bottom <= top:
        raise ValueError("Drag target has empty client bounds")
    return [left + int((right - left) * fraction[0]), top + int((bottom - top) * fraction[1])]


def _check_visible_point(record, node, point):
    screen = win32gui.ClientToScreen(node["hwnd"], tuple(point))
    by_handle = {n["hwnd"]: n for n in record["nodes"]}
    current, seen = node, set()
    while current["hwnd"] not in seen:
        seen.add(current["hwnd"])
        left, top, right, bottom = current["rect"]
        if not left <= screen[0] < right or not top <= screen[1] < bottom:
            raise ValueError("Drag endpoint is outside the visible ancestor bounds")
        if current["parent"] not in by_handle:
            break
        current = by_handle[current["parent"]]


def drag_ui(
    session_id, source_ui_id, start_fraction, end_fraction, target_ui_id=None, duration_ms=500
):
    validate_drag(start_fraction, end_fraction, duration_ms)
    session_guard(session_id)
    binary = hpe990_folders.F_HPE990_INPUT
    if not binary.is_file():
        raise FileNotFoundError(f"Build the Rust input worker first: {binary}")
    lock = hpe990_folders.D_HPE990_RUNTIME / "drag.lock"
    with FileLock(str(lock), timeout=1):
        monitor = start_ram(session_id)
        before = collect_ui(session_id, accessibility_backend="none")
        source = resolve_drag_node(before, source_ui_id)
        target = resolve_drag_node(before, target_ui_id or source_ui_id)
        if source["pid"] != target["pid"]:
            raise ValueError("Drag endpoints must belong to the same Emulator process")
        start = _point(source, start_fraction)
        end_target = _point(target, end_fraction)
        _check_visible_point(before, source, start)
        _check_visible_point(before, target, end_target)
        end_screen = win32gui.ClientToScreen(target["hwnd"], tuple(end_target))
        end = list(win32gui.ScreenToClient(source["hwnd"], end_screen))
        if any(not -32768 <= value <= 32767 for value in (*start, *end)):
            raise ValueError("Drag endpoints exceed signed 16-bit message coordinates")
        if start == end:
            raise ValueError("Drag start and end resolve to the same pixel")
        fresh = {n["hwnd"]: n for n in _native_tree(session_guard(session_id))}
        for node in (source, target):
            live = fresh.get(node["hwnd"])
            if not live or any(live[k] != node[k] for k in ("pid", "class_name", "name", "rect")):
                raise ValueError("Drag target changed during preflight collection")
        action_id = uuid.uuid4().hex
        directory = hpe990_folders.D_HPE990_EVIDENCE / "04be9d05" / session_id / action_id
        directory.mkdir(parents=True)
        request = {
            "pid": source["pid"],
            "source": source,
            "target": target,
            "start_client": start,
            "end_client": end,
            "duration_ms": duration_ms,
        }
        request_path = directory / "request.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        details = {
            "action": "drag",
            "source": source,
            "target": target,
            "start_fraction": start_fraction,
            "end_fraction": end_fraction,
            "duration_ms": duration_ms,
            "before": before["evidence"],
        }
        action_marker(session_id, action_id, "requested", details)
        receipt = None
        failure = None
        try:
            result = subprocess.run(
                [str(binary), str(request_path)],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=duration_ms / 1000 + 3,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            receipt = json.loads(result.stdout)
            if result.returncode or not receipt["ok"]:
                raise RuntimeError(f"Rust drag failed: {receipt}")
        except Exception as error:
            failure = error
        finally:
            # Timeout/process termination cannot run Rust cleanup, so release here as well.
            if (not receipt or not receipt.get("button_release_posted")) and win32gui.IsWindow(
                source["hwnd"]
            ):
                _, pid = win32process.GetWindowThreadProcessId(source["hwnd"])
                if pid == source["pid"]:
                    win32gui.PostMessage(
                        source["hwnd"], win32con.WM_LBUTTONUP, 0, win32api_position(*end)
                    )
        (directory / "receipt.json").write_text(
            json.dumps({"worker": receipt, "error": str(failure) if failure else None}),
            encoding="utf-8",
        )
        time.sleep(0.3)
        after = collect_ui(session_id, accessibility_backend="none")
        outcome = {
            "action": "drag",
            "after": after["evidence"],
            "receipt": str(directory / "receipt.json"),
            "error": str(failure) if failure else None,
        }
        action_marker(session_id, action_id, "failed" if failure else "observed", outcome)
        if failure:
            failure.hpe990_action_id = action_id
            raise failure
        return {
            "session_id": session_id,
            "action_id": action_id,
            "source": source,
            "target": target,
            "worker": receipt,
            "before": before["evidence"],
            "after": after["evidence"],
            "ram_active": ram_status(session_id)["active"],
            "ram_directory": monitor["directory"],
            "receipt": outcome["receipt"],
            "application_result_verified": False,
            "scope": "Input delivery observed; caller/BDD must verify application result",
        }

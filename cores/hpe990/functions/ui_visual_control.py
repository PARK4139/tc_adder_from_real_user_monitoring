"""Re-observe OCR IDs before converting screenshot coordinates to guarded input."""

import json
import sqlite3
from pathlib import Path

import win32gui
import win32process

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.monitoring import session_guard
from cores.hpe990.functions.ui import collect_ui, control_ui


def historical_visual(ui_id):
    if not ui_id.startswith("UI-") or not ui_id[3:].isdigit():
        raise ValueError("Invalid UI identity")
    with sqlite3.connect(hpe990_folders.F_HPE990_UI_REGISTRY) as database:
        rows = database.execute(
            "SELECT evidence FROM observations WHERE number=? AND backend='visual' ORDER BY rowid DESC LIMIT 1",
            (int(ui_id[3:]),),
        ).fetchall()
    if not rows:
        raise ValueError("No observed visual element for UI ID")
    record = json.loads(Path(rows[0][0]).read_text(encoding="utf-8"))
    elements = [e for e in record["visual"]["elements"] if e["ui_id"] == ui_id]
    if len(elements) != 1:
        raise ValueError("Ambiguous historical visual identity")
    return record["session_id"], elements[0]


def resolve_visual(record, ui_id, old=None):
    elements = record.get("visual", {}).get("elements", [])
    matches = [e for e in elements if e["ui_id"] == ui_id]
    if not matches and old is not None and old.get("name"):
        matches = [
            e
            for e in elements
            if e.get("root_ui_id") == old["root_ui_id"]
            and e.get("name") == old["name"]
            and e["control_type"] == old["control_type"]
        ]
    if len(matches) != 1:
        raise ValueError("Visual target is missing or ambiguous after recollection")
    target = matches[0]
    roots = [
        n
        for n in record["roots"]
        if n["hwnd"] == target["root_hwnd"] and n["visible"] and n["enabled"]
    ]
    if len(roots) != 1 or target.get("rect_space") != "root_screenshot_pixels":
        raise ValueError("Visual root is hidden/disabled or coordinate space is unknown")
    captures = [c for c in record["screenshots"] if c["hwnd"] == target["root_hwnd"]]
    if len(captures) != 1 or captures[0]["sha256"] != target["screenshot_sha256"]:
        raise ValueError("Stale visual image")
    return target, roots[0], captures[0]


def control_visual(session_id, ui_id, action="click"):
    if action not in ("click", "double_click"):
        raise ValueError("Visual control supports click or double_click")
    session_guard(session_id)
    old_session, old = historical_visual(ui_id)
    if old_session != session_id:
        raise ValueError("Visual identity belongs to another session")
    before = collect_ui(session_id, accessibility_backend="none")
    target, root, capture = resolve_visual(before, ui_id, old)
    if win32gui.IsIconic(root["hwnd"]):
        raise ValueError("Visual root is minimized")
    left, top, right, bottom = target["rect"]
    screen = (root["rect"][0] + int((left + right) / 2), root["rect"][1] + int((top + bottom) / 2))
    hit = win32gui.WindowFromPoint(screen)
    _, pid = win32process.GetWindowThreadProcessId(hit)
    if (
        pid != root["pid"]
        or win32gui.GetAncestor(hit, 2) != root["hwnd"]
        or not win32gui.IsWindowEnabled(hit)
    ):
        raise ValueError("Visual point is occluded, disabled or belongs to another root")
    x, y = win32gui.ScreenToClient(root["hwnd"], screen)
    _, _, width, height = win32gui.GetClientRect(root["hwnd"])
    if not 0 < x < width or not 0 < y < height:
        raise ValueError("Visual text is outside the root client area")
    result = control_ui(
        session_id,
        root["name"],
        action,
        hwnd=root["hwnd"],
        point_fraction=[x / width, y / height],
        expected_capture={"rect": root["rect"], "sha256": capture["sha256"]},
    )
    return {
        **result,
        "requested_ui_id": ui_id,
        "current_ui_id": target["ui_id"],
        "visual_target": target,
        "recollection": before["evidence"],
        "scope": "Observed OCR coordinate; individual editability and application result require verification",
    }

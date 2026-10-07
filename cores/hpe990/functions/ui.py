"""Live process-guarded native UI inventory, screenshots, and observed-control input."""

import ctypes
import hashlib
import json
import time
import uuid

import win32con
import win32gui
import win32process
import win32ui
from PIL import Image

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.accessibility import collect_accessibility
from cores.hpe990.functions.lifecycle import _windows, log_event
from cores.hpe990.functions.monitoring import action_marker, ram_status, session_guard, start_ram
from cores.hpe990.functions.tc_dynamic import sync_general_expected
from cores.hpe990.functions.ui_identity import assign_ui_ids
from cores.hpe990.functions.visual_elements import collect_visual_elements


def _native_tree(session: dict) -> list[dict]:
    pids = {p["pid"] for p in session["processes"]}
    nodes = {}

    def collect(hwnd, _):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in pids:
                nodes[hwnd] = {
                    "hwnd": hwnd,
                    "pid": pid,
                    "name": win32gui.GetWindowText(hwnd),
                    "class_name": win32gui.GetClassName(hwnd),
                    "parent": (
                        win32gui.GetParent(hwnd)
                        if win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & win32con.WS_CHILD
                        else 0
                    ),
                    "owner": win32gui.GetWindow(hwnd, win32con.GW_OWNER),
                    "visible": bool(win32gui.IsWindowVisible(hwnd)),
                    "enabled": bool(win32gui.IsWindowEnabled(hwnd)),
                    "rect": list(win32gui.GetWindowRect(hwnd)),
                }
        except win32gui.error:
            pass

    def root(hwnd, _):
        collect(hwnd, None)
        if hwnd in nodes:
            win32gui.EnumChildWindows(hwnd, collect, None)

    win32gui.EnumWindows(root, None)
    return list(nodes.values())


def _capture(hwnd: int, destination) -> dict:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0 or width * height > 16000000:
        raise ValueError("Window capture dimensions invalid")
    dc = win32gui.GetWindowDC(hwnd)
    source = win32ui.CreateDCFromHandle(dc)
    target = source.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(source, width, height)
    target.SelectObject(bitmap)
    try:
        # PrintWindow asks the target to paint into our buffer, including child widgets.
        painted = ctypes.windll.user32.PrintWindow(hwnd, target.GetSafeHdc(), 0)
        if not painted:
            target.BitBlt((0, 0), (width, height), source, (0, 0), win32con.SRCCOPY)
        image = Image.frombuffer(
            "RGB", (width, height), bitmap.GetBitmapBits(True), "raw", "BGRX", 0, 1
        )
        image.save(destination)
        return {
            "hwnd": hwnd,
            "path": str(destination),
            "size": [width, height],
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "method": "PrintWindow" if painted else "BitBlt",
        }
    finally:
        win32gui.DeleteObject(bitmap.GetHandle())
        target.DeleteDC()
        source.DeleteDC()
        win32gui.ReleaseDC(hwnd, dc)


def _belongs_to_root(node: dict, root_hwnd: int, by_handle: dict) -> bool:
    seen = set()
    while node["hwnd"] not in seen:
        if node["hwnd"] == root_hwnd:
            return True
        seen.add(node["hwnd"])
        if node["parent"] not in by_handle:
            return False
        node = by_handle[node["parent"]]
    return False


def _associate_visual_nodes(visual: dict, nodes: list[dict], roots: list[dict]) -> None:
    by_handle = {node["hwnd"]: node for node in nodes}
    roots_by_handle = {root["hwnd"]: root for root in roots}
    for element in visual["elements"]:
        if element["control_type"] != "input_field_candidate":
            continue
        root = roots_by_handle[element["root_hwnd"]]
        left, top = root["rect"][:2]
        screen_rect = [
            element["rect"][0] + left,
            element["rect"][1] + top,
            element["rect"][2] + left,
            element["rect"][3] + top,
        ]
        matches = [
            node
            for node in nodes
            if node["pid"] == root["pid"]
            and _belongs_to_root(node, root["hwnd"], by_handle)
            and all(abs(a - b) <= 2 for a, b in zip(node["rect"], screen_rect))
        ]
        element["matching_native_nodes"] = [
            {"hwnd": node["hwnd"], "name": node["name"]} for node in matches
        ]
        element["ocr_name"] = element["name"]
        if len(matches) == 1 and matches[0]["name"]:
            element["native_name"] = matches[0]["name"]
            element["name"] = matches[0]["name"].split("::")[-1]
            element["name_source"] = "unique_native_rectangle_match"
        else:
            element["name_source"] = "ocr"


def collect_ui(
    session_id: str, screenshots: bool = True, accessibility_backend: str = "msaa"
) -> dict:
    if accessibility_backend not in ("msaa", "uia", "none"):
        raise ValueError("accessibility_backend must be msaa, uia or none")
    session = session_guard(session_id)
    directory = hpe990_folders.D_HPE990_EVIDENCE / "ui" / session_id / uuid.uuid4().hex
    directory.mkdir(parents=True)
    nodes = _native_tree(session)
    native_handles = {node["hwnd"] for node in nodes}
    roots = [node for node in nodes if node["parent"] not in native_handles]
    captures = []
    errors = []
    if screenshots:
        for root in roots:
            if root["visible"] and root["class_name"] == "QWidget":
                try:
                    captures.append(_capture(root["hwnd"], directory / f"{root['hwnd']}.png"))
                except Exception as error:
                    errors.append({"hwnd": root["hwnd"], "error": str(error)})
    visual = collect_visual_elements(captures, roots)
    _associate_visual_nodes(visual, nodes, roots)
    result = {
        "schema_version": 2,
        "session_id": session_id,
        "observed_unix_ms": time.time_ns() // 1000000,
        "nodes": nodes,
        "roots": roots,
        "accessibility": collect_accessibility(roots, backend=accessibility_backend),
        "visual": visual,
        "screenshots": captures,
        "capture_errors": errors,
        "coverage_scope": "Native HWNDs plus bounded accessibility and visible visual evidence. "
        "Visual candidates are not native controls; unreadable states and unvisited paths remain unresolved.",
        "evidence": str(directory / "inventory.json"),
    }
    result["ui_registry"] = assign_ui_ids(result)
    try:
        result["tc_sync"] = sync_general_expected()
    except Exception as error:
        result["tc_sync"] = {"updated": False, "error": str(error), "executed": False}
    (directory / "inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    from cores.hpe990.functions.step_templates import template_catalog

    try:
        templates = template_catalog(session_id)
        result["step_template_sync"] = {
            key: templates[key] for key in ("element_count", "case_count", "json", "html")
        }
    except Exception as error:
        result["step_template_sync"] = {"error": str(error), "bdd_executed": False}
    (directory / "inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log_event("ui_collected", session_id=session_id, nodes=len(nodes), evidence=result["evidence"])
    return result


def control_ui(
    session_id: str,
    name: str,
    action: str = "click",
    root_hwnd: int | None = None,
    text: str | None = None,
    hwnd: int | None = None,
    point_fraction: list[float] | None = None,
) -> dict:
    session = session_guard(session_id)
    nodes = _native_tree(session)
    by_handle = {n["hwnd"]: n for n in nodes}

    def in_root(node):
        current = node["hwnd"]
        seen = set()
        while current in by_handle and current not in seen:
            if current == root_hwnd:
                return True
            seen.add(current)
            current = by_handle[current]["parent"]
        return root_hwnd is None

    def interactable(node):
        current = node["hwnd"]
        seen = set()
        while current in by_handle and current not in seen:
            ancestor = by_handle[current]
            if not ancestor["visible"] or not ancestor["enabled"]:
                return False
            seen.add(current)
            current = ancestor["parent"]
        return True

    candidates = [
        n
        for n in nodes
        if n["name"] == name
        and interactable(n)
        and in_root(n)
        and (hwnd is None or n["hwnd"] == hwnd)
    ]
    if len(candidates) != 1:
        raise ValueError(f"Expected one visible enabled control {name!r}; found {len(candidates)}")
    if action not in (
        "click",
        "double_click",
        "escape",
        "enter",
        "text",
        "scroll_down",
        "scroll_up",
    ):
        raise ValueError("Unsupported action")
    if action in ("scroll_down", "scroll_up") and name != "qt_scrollarea_viewport":
        raise ValueError("Scroll requires the observed Qt scroll-area viewport")
    node = candidates[0]
    hwnd = node["hwnd"]
    if point_fraction is not None and (
        len(point_fraction) != 2 or any(not 0 < v < 1 for v in point_fraction)
    ):
        raise ValueError("point_fraction must contain two finite values strictly between 0 and 1")
    if action == "text" and (
        text is None
        or len(text) > 4096
        or not name.lower().startswith(("lineedit", "textedit", "spinbox"))
    ):
        raise ValueError("Text requires an observed edit control and at most 4096 characters")
    monitor = start_ram(session_id)
    action_id = uuid.uuid4().hex
    before = collect_ui(session_id)
    observed = next(n for n in before["nodes"] if n["hwnd"] == hwnd)
    node.update(ui_id=observed["ui_id"], identity_scope=observed["identity_scope"])
    action_marker(
        session_id,
        action_id,
        "requested",
        {"control": node, "action": action, "before": before["evidence"]},
    )
    if action in ("click", "double_click"):
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        if right <= left or bottom <= top:
            raise ValueError("Control has an empty client area")
        fraction = point_fraction or [0.5, 0.5]
        position = win32api_position(
            left + int((right - left) * fraction[0]), top + int((bottom - top) * fraction[1])
        )
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, position)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, position)
        if action == "double_click":
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, position)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, position)
    elif action in ("scroll_down", "scroll_up"):
        rect = node["rect"]
        delta = -1200 if action == "scroll_down" else 1200
        position = win32api_position((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, (delta & 0xFFFF) << 16, position)
    elif action in ("escape", "enter"):
        key = win32con.VK_ESCAPE if action == "escape" else win32con.VK_RETURN
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)
    else:
        for character in text:
            win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(character), 0)
    log_event(
        "ui_action",
        session_id=session_id,
        action_id=action_id,
        control=node,
        action=action,
        ram_directory=monitor["directory"],
        before=before["evidence"],
    )
    time.sleep(0.3)
    after = collect_ui(session_id)
    action_marker(
        session_id,
        action_id,
        "observed",
        {"control": node, "action": action, "after": after["evidence"]},
    )
    result = {
        "session_id": session_id,
        "action_id": action_id,
        "control": node,
        "action": action,
        "ram_active": ram_status(session_id)["active"],
        "ram_directory": monitor["directory"],
        "before": before["evidence"],
        "after": after["evidence"],
        "windows": _windows(session["processes"]),
    }
    return result


def window_geometry(session_id: str, hwnd: int, rect: list[int]) -> dict:
    session = session_guard(session_id)
    nodes = _native_tree(session)
    candidates = [n for n in nodes if n["hwnd"] == hwnd and not n["parent"] and n["visible"]]
    if len(candidates) != 1:
        raise ValueError("Geometry control requires this session's visible top-level window")
    if len(rect) != 4 or any(isinstance(v, bool) for v in rect):
        raise ValueError("rect must contain four integer screen coordinates")
    left, top, right, bottom = rect
    if not 100 <= right - left <= 4096 or not 50 <= bottom - top <= 4096:
        raise ValueError("Unsupported window dimensions")
    start_ram(session_id)
    action_id = uuid.uuid4().hex
    action_marker(
        session_id,
        action_id,
        "requested",
        {
            "action": "geometry",
            "hwnd": hwnd,
            "before_rect": candidates[0]["rect"],
            "requested_rect": rect,
        },
    )
    win32gui.SetWindowPos(
        hwnd,
        0,
        left,
        top,
        right - left,
        bottom - top,
        win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER,
    )
    time.sleep(0.4)
    actual = list(win32gui.GetWindowRect(hwnd))
    action_marker(
        session_id,
        action_id,
        "observed",
        {"action": "geometry", "hwnd": hwnd, "actual_rect": actual},
    )
    log_event("geometry_action", session_id=session_id, action_id=action_id, actual_rect=actual)
    return {
        "session_id": session_id,
        "action_id": action_id,
        "hwnd": hwnd,
        "before_rect": candidates[0]["rect"],
        "requested_rect": rect,
        "actual_rect": actual,
        "ram_active": ram_status(session_id)["active"],
    }


def ui_catalog(session_id: str) -> dict:
    """Aggregate actual snapshots and control actions; never infer whole-app completeness."""
    session_guard(session_id, False)
    root = hpe990_folders.D_HPE990_EVIDENCE / "ui" / session_id
    observations = []
    controls = {}
    supplemental = {}
    supplemental_errors = []
    registry_elements = {}
    observation_controls = {}
    for path in sorted(root.glob("*/inventory.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        registry = assign_ui_ids(record)
        registry_elements.update({e["ui_id"]: e for e in registry["elements"]})
        observation_controls[str(path)] = {n["hwnd"]: n["ui_id"] for n in record["nodes"]}
        for backend in ("accessibility", "visual"):
            for element in record.get(backend, {}).get("elements", []):
                item = supplemental.setdefault(
                    element["ui_id"], {"identity": element, "observations": []}
                )
                item["observations"].append(str(path))
            for error in record.get(backend, {}).get("errors", []):
                supplemental_errors.append(
                    {"backend": backend, "evidence": str(path), "error": error}
                )
        observations.append(
            {
                "evidence": str(path),
                "observed_unix_ms": record["observed_unix_ms"],
                "nodes": len(record["nodes"]),
                "screenshots": record["screenshots"],
            }
        )
        by_handle = {n["hwnd"]: n for n in record["nodes"]}
        for node in record["nodes"]:
            key = node["ui_id"]
            current = node
            ancestry = []
            seen = set()
            while current["hwnd"] not in seen:
                seen.add(current["hwnd"])
                ancestry.append(current["name"] or current["class_name"])
                if current["parent"] not in by_handle:
                    break
                current = by_handle[current["parent"]]
            item = controls.setdefault(
                key,
                {
                    "identity": node,
                    "path": list(reversed(ancestry)),
                    "observations": [],
                    "actions": [],
                },
            )
            item["observations"].append(str(path))
    from cores.hpe990.common.paths import F_HPE990_EVENTS

    if F_HPE990_EVENTS.exists():
        for line in F_HPE990_EVENTS.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("session_id") == session_id and record["event"] == "ui_action":
                key = observation_controls.get(record.get("before"), {}).get(
                    record["control"]["hwnd"]
                )
                if key in controls:
                    controls[key]["actions"].append(
                        {"action_id": record["action_id"], "action": record["action"]}
                    )
    frontier = []
    for item in controls.values():
        name = item["identity"]["name"]
        if name.startswith(("pushButton", "widget_click")) and not item["actions"]:
            frontier.append(
                {
                    "hwnd": item["identity"]["hwnd"],
                    "ui_id": item["identity"]["ui_id"],
                    "name": name,
                    "path": item["path"],
                    "reason": "Observed control has not been explored",
                }
            )
    report = {
        "schema_version": 2,
        "session_id": session_id,
        "ui_registry": {
            "database": str(hpe990_folders.F_HPE990_UI_REGISTRY),
            "elements": list(registry_elements.values()),
            "unique_elements": len(registry_elements),
            "unresolved_identity_count": sum(
                e["identity_scope"] != "semantic_path" for e in registry_elements.values()
            ),
        },
        "observations": observations,
        "controls": list(controls.values()),
        "unique_native_controls": len(controls),
        "supplemental_elements": list(supplemental.values()),
        "unique_supplemental_elements": len(supplemental),
        "supplemental_errors": supplemental_errors,
        "unvisited_controls": frontier,
        "whole_application_complete": False,
        "limits": [
            "Native HWND collection includes unnamed controls; their appearance is "
            "preserved in screenshots, but Qt painted sub-items may lack HWND identity",
            "Unvisited data-dependent paths require a test-job corpus and "
            "confirmed safe navigation boundaries before an exhaustive claim",
        ],
    }
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "ui-inventory.json"
    report["evidence"] = str(destination)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def win32api_position(x: int, y: int) -> int:
    return (y << 16) | (x & 0xFFFF)

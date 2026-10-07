"""Collect process-scoped UI Automation elements independent of native child HWNDs."""

import json
import subprocess
import sys
from pathlib import Path


def collect_accessibility(
    roots: list[dict], timeout_seconds: float = 3, backend: str = "msaa"
) -> dict:
    """Isolate potentially unresponsive external providers in a bounded worker."""
    if backend not in ("msaa", "uia", "none"):
        raise ValueError("accessibility_backend must be msaa, uia or none")
    targets = (
        [
            root
            for root in roots
            if root["visible"] and root["enabled"] and root["class_name"] == "QWidget"
        ]
        if backend != "none"
        else []
    )
    if not targets:
        return {"backend": backend, "elements": [], "errors": [], "complete": True}
    try:
        worker = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), json.dumps(targets), backend],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout_seconds,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if worker.returncode:
            raise RuntimeError(worker.stderr.decode("utf-8", errors="replace")[-1000:])
        return json.loads(worker.stdout.decode("utf-8"))
    except subprocess.TimeoutExpired:
        return {
            "backend": backend,
            "elements": [],
            "errors": [f"Provider timed out after {timeout_seconds}s"],
            "complete": False,
        }
    except (RuntimeError, ValueError) as error:
        return {"backend": backend, "elements": [], "errors": [str(error)], "complete": False}


def uia_collect(targets: list[dict]) -> dict:
    from pywinauto import Desktop

    elements, errors = [], []
    desktop = Desktop(backend="uia")
    for root in targets:
        try:
            wrapper = desktop.window(handle=root["hwnd"]).wrapper_object()
            for element in [wrapper, *wrapper.descendants()]:
                info = element.element_info
                if info.process_id != root["pid"]:
                    continue
                rect = info.rectangle
                record = {
                    "id": f"uia:{root['hwnd']}:{'.'.join(map(str, info.runtime_id))}",
                    "backend": "uia",
                    "root_hwnd": root["hwnd"],
                    "pid": info.process_id,
                    "name": info.name,
                    "control_type": info.control_type,
                    "class_name": info.class_name,
                    "automation_id": info.automation_id,
                    "hwnd": info.handle or None,
                    "rect": [rect.left, rect.top, rect.right, rect.bottom],
                    "visible": info.visible,
                    "enabled": info.enabled,
                }
                try:
                    record["value"] = element.get_value()
                except Exception:
                    record["value"] = None
                elements.append(record)
        except Exception as error:
            errors.append({"root_hwnd": root["hwnd"], "error": str(error)})
    return {"backend": "uia", "elements": elements, "errors": errors, "complete": not errors}


def worker_collect(targets: list[dict]) -> dict:
    import ctypes
    from ctypes import wintypes

    from comtypes import POINTER
    from comtypes.client import GetModule

    accessible_type = GetModule("oleacc.dll").IAccessible
    oleacc = ctypes.OleDLL("oleacc")
    get_object = oleacc.AccessibleObjectFromWindow
    get_object.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p]
    get_object.restype = ctypes.c_long
    elements, errors = [], []

    def property_value(obj, name, child):
        try:
            return getattr(obj, name)[child]
        except Exception:
            return None

    def visit(obj, child, root, path, depth=0):
        if depth > 32 or len(elements) >= 2048:
            raise RuntimeError("MSAA traversal limit reached")
        identity = f"msaa:{root['hwnd']}:{path}"
        state = property_value(obj, "accState", child)
        try:
            left, top, width, height = obj.accLocation(child)
            rect = [left, top, left + width, top + height]
        except Exception:
            rect = None
        elements.append(
            {
                "id": identity,
                "backend": "msaa",
                "root_hwnd": root["hwnd"],
                "pid": root["pid"],
                "parent_id": None
                if path == "0"
                else f"msaa:{root['hwnd']}:{path.rsplit('.', 1)[0]}",
                "name": property_value(obj, "accName", child),
                "value": property_value(obj, "accValue", child),
                "role": property_value(obj, "accRole", child),
                "state": state,
                "rect": rect,
                "visible": None if not isinstance(state, int) else not bool(state & 0x8000),
                "enabled": None if not isinstance(state, int) else not bool(state & 1),
                "readonly": None if not isinstance(state, int) else bool(state & 0x40),
                "hwnd": None,
            }
        )
        if child:
            return
        for index in range(1, min(obj.accChildCount, 2048) + 1):
            descendant = property_value(obj, "accChild", index)
            if descendant:
                visit(
                    descendant.QueryInterface(accessible_type),
                    0,
                    root,
                    f"{path}.{index}",
                    depth + 1,
                )
            else:
                visit(obj, index, root, f"{path}.{index}", depth + 1)

    for root in targets:
        try:
            obj = POINTER(accessible_type)()
            status = get_object(
                root["hwnd"], 0xFFFFFFFC, ctypes.byref(accessible_type._iid_), ctypes.byref(obj)
            )
            if status < 0 or not obj:
                raise RuntimeError(f"AccessibleObjectFromWindow failed: {status}")
            visit(obj, 0, root, "0")
        except Exception as error:
            errors.append({"root_hwnd": root["hwnd"], "error": str(error)})
    return {"backend": "msaa", "elements": elements, "errors": errors, "complete": not errors}


if __name__ == "__main__":
    collector = uia_collect if sys.argv[2] == "uia" else worker_collect
    sys.stdout.buffer.write(
        json.dumps(collector(json.loads(sys.argv[1])), ensure_ascii=False).encode("utf-8")
    )

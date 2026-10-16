"""Validate captured UI identities and image evidence without claiming exhaustive coverage."""

import hashlib
import json
import re
from pathlib import Path

from PIL import Image

from cores.hpe990.common.paths import hpe990_folders


def audit_collection(
    session_id: str, inventory_paths: list[str], expected_screens: list[str] | None = None
) -> dict:
    """Audit explicit session snapshots; never navigate or treat delivery as success."""
    if not re.fullmatch(r"[0-9a-f]{32}", session_id):
        raise ValueError("Expected a recorded session identity")
    if not inventory_paths:
        raise ValueError("Supply at least one inventory evidence path")
    root = (hpe990_folders.D_HPE990_EVIDENCE / "ui" / session_id).resolve()
    paths = list(dict.fromkeys(Path(p).resolve() for p in inventory_paths))
    for path in paths:
        if not path.is_relative_to(root) or path.name != "inventory.json":
            raise ValueError("Inventory must belong to the specified session evidence directory")
    ids, screens, buttons, inputs, errors = set(), set(), set(), set(), []
    active_screen_names = set()
    native = supplemental = captures = 0
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("session_id") != session_id:
            raise ValueError("Inventory session mismatch")
        elements = record.get("nodes", [])
        if not elements:
            errors.append({"inventory": str(path), "reason": "empty_native_inventory"})
        native += len(elements)
        extra = [
            e
            for source in ("accessibility", "visual")
            for e in record.get(source, {}).get("elements", [])
        ]
        supplemental += len(extra)
        registered = {e.get("ui_id") for e in record.get("ui_registry", {}).get("elements", [])}
        for element in elements + extra:
            if not element.get("ui_id"):
                errors.append({"inventory": str(path), "reason": "missing_ui_id"})
            else:
                ids.add(element["ui_id"])
                name = (element.get("name") or "").lower()
                kind = (element.get("control_type") or "").lower()
                if name.startswith(("pushbutton", "btn_")) or kind == "button":
                    buttons.add(element["ui_id"])
                if name.startswith(("lineedit", "textedit", "spinbox")) or kind in (
                    "edit",
                    "spinner",
                ):
                    inputs.add(element["ui_id"])
                if element["ui_id"] not in registered:
                    errors.append(
                        {
                            "inventory": str(path),
                            "reason": "unregistered_ui_id",
                            "ui_id": element["ui_id"],
                        }
                    )
        screenshots = record.get("screenshots", [])
        captured = {s.get("hwnd") for s in screenshots}
        for screen in record.get("roots", []):
            if screen.get("visible"):
                if screen.get("enabled") and screen.get("name"):
                    active_screen_names.add(screen["name"])
                if not screen.get("ui_id"):
                    errors.append({"inventory": str(path), "reason": "missing_screen_ui_id"})
                screens.add(screen.get("ui_id"))
                if screen["hwnd"] not in captured:
                    errors.append({"inventory": str(path), "reason": "missing_screen_capture"})
        for capture in screenshots:
            image = Path(capture["path"]).resolve()
            if not image.is_relative_to(root):
                raise ValueError("Capture must belong to the specified session")
            captures += 1
            if not image.is_file():
                errors.append(
                    {"inventory": str(path), "reason": "missing_image", "path": str(image)}
                )
            elif hashlib.sha256(image.read_bytes()).hexdigest() != capture.get("sha256"):
                errors.append({"inventory": str(path), "reason": "image_hash_mismatch"})
            else:
                try:
                    with Image.open(image) as png:
                        if png.format != "PNG":
                            raise ValueError("Expected PNG")
                        png.verify()
                except (OSError, ValueError) as error:
                    errors.append(
                        {"inventory": str(path), "reason": "invalid_png", "detail": str(error)}
                    )
            if capture.get("quality_flags"):
                errors.append(
                    {
                        "inventory": str(path),
                        "reason": "capture_quality",
                        "flags": capture["quality_flags"],
                    }
                )
        for source in ("capture_errors",):
            errors.extend(
                {"inventory": str(path), "reason": source, "detail": e}
                for e in record.get(source, [])
            )
        for backend in ("accessibility", "visual"):
            errors.extend(
                {"inventory": str(path), "reason": f"{backend}_error", "detail": error}
                for error in record.get(backend, {}).get("errors", [])
            )
    for name in expected_screens or []:
        if name not in active_screen_names:
            errors.append({"reason": "missing_expected_screen", "screen": name})
    return {
        "session_id": session_id,
        "inventory_count": len(paths),
        "unique_ui_ids": len(ids),
        "visible_root_ids": len(screens),
        "active_screen_names": sorted(active_screen_names),
        "expected_screens": expected_screens or [],
        "identified_button_ids": len(buttons),
        "identified_input_ids": len(inputs),
        "type_count_scope": "Named native controls and accessibility types only; unnamed/OCR candidates may be unresolved",
        "visibility_scope": "Native visibility flags may include controls clipped by scroll viewports; they do not prove on-screen visibility",
        "native_observations": native,
        "supplemental_observations": supplemental,
        "image_count": captures,
        "errors": errors,
        "evidence_verdict": "PASS" if not errors else "FAIL",
        "whole_application_complete": False,
        "application_result_verified": False,
        "scope": "Explicit captured snapshots only; hidden/unvisited paths remain unverified",
        "inventory_paths": [str(p) for p in paths],
    }

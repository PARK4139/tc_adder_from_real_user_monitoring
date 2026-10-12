"""Derived per-UI-ID input ledger; unknown editability is never omitted."""

import json
from collections import Counter

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.monitoring import session_guard


def input_kind(element, backend):
    name = (element.get("name") or "").lower()
    if backend == "visual" and element.get("control_type") == "input_field_candidate":
        return "visual_input_candidate"
    if backend == "accessibility" and (
        element.get("control_type") == "Edit" or element.get("role") == 42
    ):
        return "provider_edit"
    if backend == "native" and (
        name.startswith(("lineedit", "textedit", "plaintextedit", "spinbox", "doublespinbox"))
        or name.startswith("ui_general::input::")
    ):
        return "native_input_hint"
    return None


def build_input_ledger(records):
    inputs = {}
    for record in sorted(records, key=lambda r: r.get("observed_unix_ms", 0)):
        for backend, elements in (
            ("native", record["nodes"]),
            ("accessibility", record.get("accessibility", {}).get("elements", [])),
            ("visual", record.get("visual", {}).get("elements", [])),
        ):
            for element in elements:
                kind = input_kind(element, backend)
                if kind is None:
                    continue
                identity = element["ui_id"]
                entry = inputs.setdefault(
                    identity,
                    {
                        "ui_id": identity,
                        "name": element.get("name"),
                        "editability": "unknown",
                        "editability_basis": "unverified",
                        "replacement_verified": False,
                        "observations": [],
                    },
                )
                if kind == "provider_edit" and element.get("readonly") is not None:
                    entry["editability"] = (
                        "readonly" if element["readonly"] else "provider_editable"
                    )
                    entry["editability_basis"] = "provider_state; actual replacement unverified"
                observation = {
                    "backend": backend,
                    "kind": kind,
                    "observed_unix_ms": record.get("observed_unix_ms"),
                    "evidence": record["evidence"],
                    "name": element.get("name"),
                    "root_hwnd": element.get("root_hwnd"),
                    "hwnd": element.get("hwnd"),
                    "visible": element.get("visible"),
                    "enabled": element.get("enabled"),
                    "value": element.get("value"),
                    "ocr_text": element.get("observed_text"),
                    "screenshot": element.get("screenshot"),
                    "rect": element.get("rect"),
                }
                entry["observations"].append(observation)
                entry["latest"] = observation
    return {
        "inputs": sorted(inputs.values(), key=lambda entry: int(entry["ui_id"][3:])),
        "summary": {
            "input_count": len(inputs),
            "editability": dict(Counter(e["editability"] for e in inputs.values())),
            "replacement_verified_count": 0,
        },
        "scope": "Observed input candidates, including hidden/readonly/unknown; not whole-application coverage",
    }


def input_inventory(session_id):
    session_guard(session_id, False)
    root = hpe990_folders.D_HPE990_EVIDENCE / "ui" / session_id
    records, errors = [], []
    for path in root.glob("*/inventory.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["session_id"] != session_id:
                raise ValueError("Snapshot session mismatch")
            records.append(record)
        except (OSError, ValueError, KeyError) as error:
            errors.append({"source": str(path), "error": str(error)})
    report = {
        "session_id": session_id,
        **build_input_ledger(records),
        "source_count": len(records),
        "errors": errors,
    }
    directory = hpe990_folders.D_HPE990_EVIDENCE / "214bb297" / session_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "input-inventory.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**report, "evidence": str(path)}

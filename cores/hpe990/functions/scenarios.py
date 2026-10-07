"""Registered Gherkin and observed-transition traceability, exposed through MCP."""

import json
from pathlib import Path

from cores.common.functions.run_family_bdd import bdd_registry
from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.analysis import analyze_ui
from cores.hpe990.functions.lifecycle import log_event


def scenario_catalog(session_id: str | None = None) -> dict:
    registry = bdd_registry("hpe990")
    if session_id is None:
        return registry
    analysis = analyze_ui(session_id)
    states = {s["id"]: s for s in analysis["states"]}
    feature = next(s for s in registry["scenarios"] if s["test"] == "test_launch_to_stop_workflow")
    mappings = []
    for transition in analysis["transitions"]:
        destination = states[transition["to"]]
        names = {r["name"] for r in destination["visible_roots"]}
        if transition["to"] == "S-application-stopped":
            step = "I stop the owned Emulator application explicitly"
        elif "Shutdown" in names:
            step = "I open Setup and its Shutdown confirmation"
        elif any(r["name"] == "Setup" and r["enabled"] for r in destination["visible_roots"]):
            source_names = {r["name"] for r in states[transition["from"]]["visible_roots"]}
            step = (
                "I cancel the Shutdown confirmation"
                if "Shutdown" in source_names
                else "I open Setup and its Shutdown confirmation"
            )
        elif any(r["name"] == "Edger" and r["enabled"] for r in destination["visible_roots"]):
            step = "I launch the Emulator and continue into Edger"
        else:
            step = None
        mappings.append(
            {
                "transition": transition["id"],
                "from": transition["from"],
                "to": transition["to"],
                "step": step,
                "evidence": transition["evidence"],
                "scenario": feature["name"] if step else None,
            }
        )
    missing = [m["transition"] for m in mappings if m["step"] not in feature["steps"]]
    result = {
        "schema_version": 1,
        "session_id": session_id,
        "registry": registry,
        "analysis": analysis["evidence"],
        "mappings": mappings,
        "missing_required_transitions": missing,
        "mapping_coverage_percent": 100 if mappings and not missing else 0,
        "scope": "Observed startup/Edger/Setup/Shutdown-cancel/application-stop workflow; "
        "additional observed paths must receive scenarios before expanding this acceptance set",
        "verdict": "PASS" if mappings and not missing else "FAIL",
    }
    directory = hpe990_folders.D_HPE990_EVIDENCE / "093ca349" / session_id
    directory.mkdir(parents=True, exist_ok=True)
    result["evidence"] = str(directory / "traceability.json")
    Path(result["evidence"]).write_text(json.dumps(result, indent=2), encoding="utf-8")
    log_event(
        "bdd_scenarios_mapped",
        session_id=session_id,
        evidence=result["evidence"],
        missing=len(missing),
    )
    return result

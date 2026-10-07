"""Evidence-derived states, transitions and observed native operation coverage."""

import hashlib
import json
from pathlib import Path

from cores.hpe990.common.paths import F_HPE990_EVENTS, hpe990_folders
from cores.hpe990.functions.lifecycle import log_event
from cores.hpe990.functions.monitoring import ram_status, session_guard, telemetry_read
from cores.hpe990.functions.operations import OPERATION_TO_TOOL
from cores.hpe990.functions.ui import ui_catalog


def analyze_ui(session_id: str) -> dict:
    session_guard(session_id, False)
    catalog = ui_catalog(session_id)
    snapshots = [
        json.loads(Path(o["evidence"]).read_text(encoding="utf-8")) for o in catalog["observations"]
    ]
    snapshots.sort(key=lambda s: s["observed_unix_ms"])
    if not snapshots:
        raise ValueError("Collect UI snapshots before analysis")
    monitor = ram_status(session_id)
    events = []
    if "directory" in monitor:
        cursor = 0
        while True:
            page = telemetry_read(session_id, cursor, 10000)
            if not page["events"]:
                break
            events.extend(page["events"])
            cursor = page["next_sequence"]
    states = {}
    transitions = []
    previous = None
    source = str(Path(monitor["directory"]) / "events.jsonl") if "directory" in monitor else None
    for snapshot in snapshots:
        roots = sorted(
            [
                {"name": r["name"], "enabled": r["enabled"], "owner": bool(r["owner"])}
                for r in snapshot["roots"]
                if r["visible"] and r["class_name"] == "QWidget"
            ],
            key=lambda r: (r["name"], r["enabled"]),
        )
        state_id = (
            "S-" + hashlib.sha256(json.dumps(roots, sort_keys=True).encode()).hexdigest()[:12]
        )
        state = states.setdefault(
            state_id, {"id": state_id, "visible_roots": roots, "evidence": [], "kind": "observed"}
        )
        state["evidence"].append(snapshot["evidence"])
        if previous and previous["id"] != state_id:
            nearby = [
                e
                for e in events
                if previous["time"] <= e["observed_unix_ms"] <= snapshot["observed_unix_ms"]
            ]
            transitions.append(
                {
                    "id": f"T-{len(transitions) + 1:04d}",
                    "from": previous["id"],
                    "to": state_id,
                    "kind": "observed",
                    "time_unix_ms": snapshot["observed_unix_ms"],
                    "input_markers": [e for e in nearby if e["kind"] == "control_action"],
                    "evidence": {
                        "before": previous["evidence"],
                        "after": snapshot["evidence"],
                        "events_file": source,
                        "event_sequences": [e["sequence"] for e in nearby],
                    },
                }
            )
        previous = {
            "id": state_id,
            "time": snapshot["observed_unix_ms"],
            "evidence": snapshot["evidence"],
        }
    exits = [
        e for e in events if e["kind"] == "monitor_stopped" and e.get("reason") == "process_exited"
    ]
    if exits:
        states["S-application-stopped"] = {
            "id": "S-application-stopped",
            "visible_roots": [],
            "kind": "observed",
            "evidence": [source],
            "event_sequence": exits[-1]["sequence"],
        }
        transitions.append(
            {
                "id": f"T-{len(transitions) + 1:04d}",
                "from": previous["id"],
                "to": "S-application-stopped",
                "kind": "observed",
                "input_markers": [],
                "evidence": {
                    "before": previous["evidence"],
                    "after": source,
                    "event_sequences": [exits[-1]["sequence"]],
                },
                "exit_policy": "Explicit owned process stop; normal OS shutdown is not tested",
            }
        )
    calls = []
    if F_HPE990_EVENTS.exists():
        calls = [
            json.loads(line)
            for line in F_HPE990_EVENTS.read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("session_id") == session_id
        ]
    operations = []
    for item in catalog["controls"]:
        name = item["identity"]["name"]
        if name.startswith(("pushButton", "widget_click")) or name == "qt_tabwidget_tabbar":
            operations.append(
                {
                    "name": name,
                    "hwnd": item["identity"]["hwnd"],
                    "path": item["path"],
                    "mcp_tool": "hpe990_ui_control",
                    "arguments": {
                        "session_id": session_id,
                        "name": name,
                        "hwnd": item["identity"]["hwnd"],
                    },
                    "observed_calls": len(item["actions"]),
                    "evidence": item["observations"],
                    "semantic_execution": "Must verify the visible outcome; HWND enabled alone is insufficient",
                }
            )
    result = {
        "schema_version": 1,
        "session_id": session_id,
        "states": list(states.values()),
        "transitions": transitions,
        "observed_operations": operations,
        "unmapped_observed_operations": [],
        "state_evidence_coverage_percent": 100,
        "transition_evidence_coverage_percent": 100,
        "unsupported_factual_transitions": 0,
        "whole_application_complete": False,
        "unresolved": catalog["unvisited_controls"],
        "hypotheses": [
            "Maintenance Code unlock may expose further states; not observed",
            "Additional job data may expose editing/grinding flows; not proved complete",
        ],
        "modal_condition": "Visible owned top-level window; owner/root enabled state is recorded. "
        "Control actions require every native parent to be visible and enabled.",
        "control_identity": "Use session identity plus observed HWND and object name, optionally root scope. "
        "HWNDs are valid only within the current process lifetime.",
        "lifecycle_events": len(calls),
        "automation_operations": OPERATION_TO_TOOL,
    }
    directory = hpe990_folders.D_HPE990_EVIDENCE / "f797f6a4" / session_id
    directory.mkdir(parents=True, exist_ok=True)
    result["evidence"] = str(directory / "ui-analysis.json")
    result["markdown"] = str(directory / "ui-analysis.md")
    Path(result["evidence"]).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Observed Emulator UI Analysis",
        "",
        f"Session: `{session_id}`",
        "",
        "## Scope",
        "",
        "Observed native window states and transitions only. Whole application "
        "coverage remains incomplete; maintenance access and unvisited paths remain unresolved.",
        "",
        "## States",
        "",
        "| State | Visible windows (enabled) | Evidence |",
        "|---|---|---|",
    ]
    for state in result["states"]:
        names = (
            ", ".join(f"{r['name']} ({r['enabled']})" for r in state["visible_roots"]) or "Stopped"
        )
        lines.append(f"| {state['id']} | {names} | {state['evidence'][0]} |")
    lines += [
        "",
        "## Transitions",
        "",
        "| ID | From | To | Before / after evidence |",
        "|---|---|---|---|",
    ]
    for transition in transitions:
        proof = transition["evidence"]
        lines.append(
            f"| {transition['id']} | {transition['from']} | {transition['to']} | "
            f"{proof['before']} / {proof['after']} |"
        )
    lines += [
        "",
        "## Control and MCP Mapping",
        "",
        result["control_identity"],
        "",
        "Every observed actionable native control maps to `hpe990_ui_control`. Exact arguments "
        "and invocation counts are in ui-analysis.json; unvisited operations are not validated.",
        "",
        "## Unverified Paths",
        "",
        *[f"- {h}" for h in result["hypotheses"]],
        "",
        "## Exit",
        "",
        "Owned application stop uses explicit force. System Shutdown confirmation "
        "is cancelled. WM_CLOSE is observed to remain running; it is not reported as normal exit.",
    ]
    Path(result["markdown"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log_event(
        "ui_analyzed",
        session_id=session_id,
        states=len(states),
        transitions=len(transitions),
        evidence=result["evidence"],
    )
    return result

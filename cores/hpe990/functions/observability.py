"""Read-only boundary and live observer health for UI Automation & Observability."""

from cores.hpe990.functions.monitoring import ram_status
from cores.hpe990.functions.rum import rum_status
from cores.hpe990.functions.semantic_ram import semantic_status


def automation_observability_status(session_id: str | None = None) -> dict:
    """Describe components; optionally inspect existing observers without starting them."""
    observation = {
        "component": "ui_observation",
        "status": "NOT_QUERIED",
        "responsibilities": ["window_events", "ui_state_changes", "sampling_health", "evidence"],
        "may_inject_input": False,
        "event_origin": "unknown_unless_explicitly_attributed",
        "legacy_mcp_prefixes": ["hpe990_ram_", "hpe990_telemetry_"],
    }
    if session_id is not None:
        observation.update(
            status="QUERIED",
            native=ram_status(session_id),
            semantic=semantic_status(session_id),
        )
    return {
        "name": "UI Automation & Observability",
        "session_id": session_id,
        "ui_automation": {
            "component": "ui_automation",
            "responsibilities": ["discovery", "mapping", "navigation", "input", "outcome_checks"],
            "may_inject_input": True,
            "interaction_origin": "automation",
            "whole_application_coverage": "UNVERIFIED",
        },
        "ui_observation": observation,
        "rum": rum_status(),
        "execution_status": "NOT_RUN",
    }

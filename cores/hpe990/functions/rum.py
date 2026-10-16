"""Real-user measurement boundary; UI observers do not establish user provenance."""


def rum_status() -> dict:
    """Report instrumentation capability without manufacturing metrics from Real Activity Monitoring."""
    return {
        "component": "rum",
        "status": "NOT_IMPLEMENTED",
        "real_user_instrumentation": False,
        "metrics": None,
        "missing_capabilities": [
            "attributed_real_user_sessions",
            "real_user_interaction_to_response_measurement",
            "correlated_application_errors",
        ],
        "responsibilities": ["real_user_latency", "application_errors", "user_experience"],
        "may_inject_input": False,
        "automation_evidence_is_real_user_data": False,
    }

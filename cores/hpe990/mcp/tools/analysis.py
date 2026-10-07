"""Public evidence-derived UI analysis."""

from cores.hpe990.functions.analysis import analyze_ui


def hpe990_ui_analyze(session_id: str) -> dict:
    """Generate observed state/transition tables, snapshot/event proof and native-operation MCP mapping.

    Mark unvisited functions and hypotheses explicitly; never assert complete application coverage.
    Analysis works after the current owned session ends, using its preserved evidence.
    """
    return analyze_ui(session_id)

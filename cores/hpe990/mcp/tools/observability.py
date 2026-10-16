"""Read-only component boundaries and real-user instrumentation capability."""

from cores.hpe990.functions.observability import automation_observability_status
from cores.hpe990.functions.rum import rum_status


def hpe990_automation_observability_status(session_id: str | None = None) -> dict:
    """Read UI Automation & Observability responsibilities and optional observer health.

    No navigation, input injection, worker start or test execution. Existing Real Activity Monitoring is UI
    observation; real-user metrics remain unavailable until RUM is instrumented.
    """
    return automation_observability_status(session_id)


def hpe990_rum_status() -> dict:
    """Read RUM capability status; NOT_IMPLEMENTED, metrics=null until instrumented.

    Does not relabel automation actions or unknown-origin window events as real-user data.
    """
    return rum_status()

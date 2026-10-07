"""Public live UI observation and control operations."""

import uuid

from cores.hpe990.functions.lifecycle import log_event
from cores.hpe990.functions.monitoring import action_marker, ram_status, session_guard
from cores.hpe990.functions.ui import collect_ui, control_ui, ui_catalog, window_geometry
from cores.hpe990.functions.ui_drag import drag_ui
from cores.hpe990.functions.ui_viewer import stop_ui_viewer, visualize_ui


def hpe990_ui_drag(
    session_id: str,
    source_ui_id: str,
    start_fraction: list[float],
    end_fraction: list[float],
    target_ui_id: str | None = None,
    duration_ms: int = 500,
) -> dict:
    """Drag between currently observed native UI IDs using paced process-scoped messages.

    Fractions lie strictly inside the source/target client areas. target_ui_id defaults
    to source_ui_id. Validate the resulting UI state; delivery is not application success.
    Rust and timeout cleanup release the mouse button; RAM records before/after evidence.
    """
    try:
        return drag_ui(
            session_id, source_ui_id, start_fraction, end_fraction, target_ui_id, duration_ms
        )
    except Exception as error:
        try:
            session_guard(session_id)
            if not getattr(error, "hpe990_action_id", None) and ram_status(session_id)["active"]:
                action_marker(
                    session_id,
                    uuid.uuid4().hex,
                    "failed",
                    {
                        "action": "drag",
                        "source_ui_id": source_ui_id,
                        "target_ui_id": target_ui_id,
                        "error_type": type(error).__name__,
                    },
                )
        except (ValueError, RuntimeError, TimeoutError):
            pass
        raise


def hpe990_ui_visualize(session_id: str | None = None, open_browser: bool = True) -> dict:
    """Open the BDD-only scenario screen in the existing HTML location.

    Lists validated scenarios, issue/AC tags, bindings and original Given/When/Then.
    Registry changes refresh every 3 seconds; collected UI is not required or displayed.
    session_id is retained in the call contract but does not filter repository scenarios.
    Survives MCP disconnects; use hpe990_ui_viewer_stop to close its server.
    """
    return visualize_ui(session_id, open_browser)


def hpe990_ui_viewer_stop() -> dict:
    """Stop the local UI visualization server without touching Emulator or RAM."""
    return stop_ui_viewer()


def hpe990_ui_collect(
    session_id: str, screenshots: bool = True, accessibility_backend: str = "msaa"
) -> dict:
    """Collect HWNDs, accessibility and screenshot-derived labels/input-frame candidates.

    accessibility_backend: msaa (default), uia or none; provider requests time out after 3s.
    Visual elements have root HWNDs, source PNGs and coordinates, but no child HWND or
    verified value/editability. Disabling screenshots also disables visual collection.
    Every element has a persistent ui_id registered in the family SQLite SSOT.
    identity_scope distinguishes reusable semantic paths from unresolved session identities.
    Successful collection refreshes TC-010's marked General display expectations from
    the identity registry; tc_sync reports generation status, never a test execution result.
    """
    return collect_ui(session_id, screenshots, accessibility_backend)


def hpe990_ui_control(
    session_id: str,
    name: str,
    action: str = "click",
    root_hwnd: int | None = None,
    text: str | None = None,
    hwnd: int | None = None,
    point_fraction: list[float] | None = None,
) -> dict:
    """Operate one uniquely identified live control while RAM records before/after evidence.

    Supported actions: click, double_click, escape, enter, text, scroll_down, scroll_up.
    Scroll targets the observed Qt scroll-area viewport. Ambiguous, hidden,
    disabled, stale or foreign controls are rejected. root_hwnd scopes duplicate names.
    Text input is restricted to observed edit controls. No arbitrary screen coordinates.
    """
    try:
        return control_ui(session_id, name, action, root_hwnd, text, hwnd, point_fraction)
    except Exception as error:
        try:
            session_guard(session_id)
            if ram_status(session_id)["active"]:
                action_id = uuid.uuid4().hex
                action_marker(
                    session_id,
                    action_id,
                    "failed",
                    {"action": action, "control_name": name, "error_type": type(error).__name__},
                )
                log_event(
                    "ui_action_failed",
                    session_id=session_id,
                    action_id=action_id,
                    error_type=type(error).__name__,
                )
        except (ValueError, RuntimeError, TimeoutError):
            pass  # A stale/foreign session is never modified to record a rejected request.
        raise


def hpe990_ui_catalog(session_id: str) -> dict:
    """Read the UI identity SSOT and aggregate observations by ui_id.

    ui_registry contains canonical identity definitions for this session's elements.
    Legacy evidence is indexed without overwriting its original snapshot files.
    """
    return ui_catalog(session_id)


def hpe990_window_geometry(session_id: str, hwnd: int, rect: list[int]) -> dict:
    """Move/resize one identity-checked session window while RAM records requested/actual bounds."""
    return window_geometry(session_id, hwnd, rect)

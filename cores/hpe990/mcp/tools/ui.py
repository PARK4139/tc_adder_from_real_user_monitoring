"""Public live UI observation and control operations."""

import uuid

from cores.hpe990.functions.lifecycle import log_event
from cores.hpe990.functions.monitoring import action_marker, ram_status, session_guard
from cores.hpe990.functions.ui import collect_ui, control_ui, ui_catalog, window_geometry
from cores.hpe990.functions.ui_drag import drag_ui
from cores.hpe990.functions.ui_viewer import stop_ui_viewer, visualize_ui


def hpe990_ui_activate(session_id: str, ui_id: str) -> dict:
    """Activate a live native UI ID, restoring its minimized root, without sending keys.

    Connects helper, foreground and target input queues for the operation only.
    Verifies foreground and focus; unsupported/blocked targets fail with diagnostic trace.
    Never changes system foreground policy or sends synthetic Alt/caption clicks.
    """
    from cores.hpe990.functions.ui_keyboard import activate_ui

    return activate_ui(session_id, ui_id)


def hpe990_window_minimize(session_id: str, ui_id: str) -> dict:
    """Minimize an observed enabled native root without closing it; RAM remains active.

    Use hpe990_ui_activate on its UI ID to restore and activate it again.
    """
    from cores.hpe990.functions.ui_keyboard import minimize_ui

    return minimize_ui(session_id, ui_id)


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
    session_id: str,
    screenshots: bool = True,
    accessibility_backend: str = "msaa",
    refresh_templates: bool = True,
) -> dict:
    """Collect HWNDs, accessibility and screenshot-derived labels/input-frame candidates.

    accessibility_backend: msaa (default), uia or none; provider requests time out after 3s.
    Visual elements have root HWNDs, source PNGs and coordinates, but no child HWND or
    verified value/editability. Disabling screenshots also disables visual collection.
    Every element has a persistent ui_id registered in the family SQLite SSOT.
    identity_scope distinguishes reusable semantic paths from unresolved session identities.
    Successful collection refreshes TC-010's marked General display expectations from
    the identity registry; tc_sync reports generation status, never a test execution result.
    Set refresh_templates=false during repeated collection to defer aggregate draft export;
    screenshots, provider evidence and UI-ID registration are still retained. Finish the
    batch with hpe990_tc_templates to regenerate bindings for all newly observed IDs.
    """
    return collect_ui(session_id, screenshots, accessibility_backend, refresh_templates)


def hpe990_ui_control(
    session_id: str,
    name: str,
    action: str = "click",
    root_hwnd: int | None = None,
    text: str | None = None,
    hwnd: int | None = None,
    point_fraction: list[float] | None = None,
    refresh_templates: bool = True,
) -> dict:
    """Operate one uniquely identified live control while RAM records before/after evidence.

    Supported actions: click, double_click, escape, enter, text, scroll_down, scroll_up.
    Scroll targets the observed Qt scroll-area viewport. Ambiguous, hidden,
    disabled, stale or foreign controls are rejected. root_hwnd scopes duplicate names.
    Text input is restricted to observed edit controls. No arbitrary screen coordinates.
    refresh_templates=false defers draft export for both snapshots only; UI registration
    and RAM evidence remain active. Complete batches with hpe990_tc_templates.
    """
    try:
        return control_ui(
            session_id,
            name,
            action,
            root_hwnd,
            text,
            hwnd,
            point_fraction,
            refresh_templates=refresh_templates,
        )
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


def hpe990_ui_keys(session_id: str, ui_id: str, keys: list[str]) -> dict:
    """Deliver key chords/sequences to one current native UI ID with RAM active.

    Examples: ["Ctrl+A"], ["Home", "Shift+End"], ["F6", "Escape"].
    Supports Ctrl/Alt/Shift/Win, A-Z, 0-9, F1-F24 and named navigation/edit keys.
    Rejects stale/disabled targets, unknown keys and pre-held modifiers. System shortcuts
    can leave the application; delivery receipts do not imply an application action.
    """
    from cores.hpe990.functions.ui_keyboard import keys_ui

    return keys_ui(session_id, ui_id, keys)


def hpe990_ui_control_visual(session_id: str, ui_id: str, action: str = "click") -> dict:
    """Recollect and click an observed OCR UI ID; never reuse old screenshot coordinates.

    Rebind a changed visual ID only for one unique same-root label/type. Reject missing,
    ambiguous, minimized, stale-image, disabled-root or occluded targets. Individual
    element editability remains unknown unless separately observed. Returns RAM evidence.
    """
    from cores.hpe990.functions.ui_visual_control import control_visual

    return control_visual(session_id, ui_id, action)


def hpe990_window_geometry(session_id: str, hwnd: int, rect: list[int]) -> dict:
    """Move/resize one identity-checked session window while RAM records requested/actual bounds."""
    return window_geometry(session_id, hwnd, rect)


def hpe990_ui_input_inventory(session_id: str) -> dict:
    """List all collected input candidates by UI ID, including hidden/readonly/unknown.

    Derives evidence from this session's snapshots. Provider editability is reported
    separately from actual replacement verification. Does not modify input values.
    """
    from cores.hpe990.functions.ui_inputs import input_inventory

    return input_inventory(session_id)

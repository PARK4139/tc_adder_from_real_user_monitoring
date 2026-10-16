"""Public version-aware semantic UI mapping and guarded native control."""

from cores.hpe990.functions.ui_mapping import control_semantic, mapping, resolve_current


def hpe990_ui_map(
    session_id: str,
    action: str = "observe",
    semantic_id: str | None = None,
    ui_id: str | None = None,
    include_observations: bool = False,
) -> dict:
    """Observe/catalog version maps, explicitly verify one current UI ID, or revoke.

    verify confirms an identity mapping, never the application's functional result.
    Each executable hash needs its own confirmation; new versions remain candidates.
    All observed native names and parent paths are retained in the existing UI SSOT.
    """
    return mapping(session_id, action, semantic_id, ui_id, include_observations)


def hpe990_ui_resolve(session_id: str, semantic_id: str) -> dict:
    """Resolve a confirmed semantic ID to one freshly observed native element.

    Refuse unconfirmed versions, changed definitions/ancestry, ambiguity, hidden or
    disabled targets. HWNDs are current-session addresses, not reusable identities.
    """
    return resolve_current(session_id, semantic_id)


def hpe990_ui_control_semantic(
    session_id: str,
    semantic_id: str,
    action: str = "click",
    text: str | None = None,
    point_fraction: list[float] | None = None,
) -> dict:
    """Resolve the current confirmed version map and control it with native Real Activity Monitoring evidence.

    Existing control actions/limits apply. Delivery does not imply application success.
    """
    return control_semantic(session_id, semantic_id, action, text, point_fraction)

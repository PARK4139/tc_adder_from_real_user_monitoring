"""Canonical UI identity maintenance through the public MCP interface."""

from cores.hpe990.functions.identity_backup import backup_identity_authority


def hpe990_ui_registry_backup(session_id: str, timeout_seconds: int = 60) -> dict:
    """Snapshot canonical UI IDs/counters/maps while Real Activity Monitoring and UI collection remain active.

    Uses WAL and a bounded read transaction. Historical observations, aliases and Real Activity Monitoring
    files stay in the original storage; this is not a full historical backup.
    An interrupted/timed-out snapshot is never published. timeout_seconds: 1..300.
    """
    return backup_identity_authority(session_id, timeout_seconds)

"""Public RAM and local telemetry MCP operations."""

from cores.hpe990.functions.monitoring import (
    ram_status,
    start_ram,
    stop_ram,
    telemetry_export,
    telemetry_read,
)


def hpe990_ram_start(session_id: str, interval_ms: int = 100) -> dict:
    """Continuously observe the session's WinEvents and native HWND hierarchy in Rust."""
    return start_ram(session_id, interval_ms)


def hpe990_ram_status(session_id: str) -> dict:
    """Read worker identity, activity, last hierarchy snapshot and finalized timing metrics."""
    return ram_status(session_id)


def hpe990_ram_stop(session_id: str) -> dict:
    """Stop only this session's RAM worker, flushing its sequenced events and timing report."""
    return stop_ram(session_id)


def hpe990_telemetry_read(session_id: str, after_sequence: int = 0, limit: int = 200) -> dict:
    """Read versioned local JSONL events by sequence cursor; no network transmission."""
    return telemetry_read(session_id, after_sequence, limit)


def hpe990_telemetry_export(session_id: str) -> dict:
    """Export this RAM run's local JSONL and validate sequence/session/run/schema integrity."""
    return telemetry_export(session_id)

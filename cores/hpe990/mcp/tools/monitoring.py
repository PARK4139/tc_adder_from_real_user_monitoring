"""UI observation and local evidence operations; legacy Real Activity Monitoring names are not RUM."""

from cores.hpe990.functions.monitoring import (
    ram_status,
    start_ram,
    stop_ram,
    telemetry_export,
    telemetry_read,
)
from cores.hpe990.functions.semantic_ram import (
    semantic_read,
    semantic_start,
    semantic_status,
    semantic_stop,
)


def hpe990_ram_semantic_start(
    session_id: str, interval_ms: int = 250, accessibility_backend: str = "msaa"
) -> dict:
    """Start RGB-zero-threshold/image/OCR/readable-value monitoring alongside native Real Activity Monitoring."""
    return semantic_start(session_id, interval_ms, accessibility_backend)


def hpe990_ram_semantic_status(session_id: str) -> dict:
    """Read semantic worker health, actual sample gaps and latest image/text evidence."""
    return semantic_status(session_id)


def hpe990_ram_semantic_stop(session_id: str) -> dict:
    """Flush and stop only the semantic observer; preserve Emulator and native Real Activity Monitoring."""
    return semantic_stop(session_id)


def hpe990_ram_semantic_read(session_id: str, after_sequence: int = 0, limit: int = 200) -> dict:
    """Read RGB regions, before/after images and text/value deltas from the semantic stream."""
    return semantic_read(session_id, after_sequence, limit)


def hpe990_ram_start(session_id: str, interval_ms: int = 100) -> dict:
    """Continuously observe the session's WinEvents and native HWND hierarchy in Rust."""
    return start_ram(session_id, interval_ms)


def hpe990_ram_status(session_id: str) -> dict:
    """Read worker identity, activity, last hierarchy snapshot and finalized timing metrics."""
    return ram_status(session_id)


def hpe990_ram_stop(session_id: str) -> dict:
    """Stop only this session's Real Activity Monitoring worker, flushing its sequenced events and timing report."""
    return stop_ram(session_id)


def hpe990_telemetry_read(session_id: str, after_sequence: int = 0, limit: int = 200) -> dict:
    """Read versioned local JSONL events by sequence cursor; no network transmission."""
    return telemetry_read(session_id, after_sequence, limit)


def hpe990_telemetry_export(session_id: str) -> dict:
    """Export this Real Activity Monitoring run's local JSONL and validate sequence/session/run/schema integrity."""
    return telemetry_export(session_id)

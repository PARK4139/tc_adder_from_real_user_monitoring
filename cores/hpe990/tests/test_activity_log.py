"""Verify source fidelity, restart deduplication, partial writes and fair draining."""

import json
import threading
import time
from datetime import datetime

import pytest

from cores.hpe990.functions.activity_log import ActivityMirror


def event(sequence, run="run-1", kind="value_changed"):
    return {
        "sequence": sequence,
        "run_id": run,
        "session_id": "a" * 32,
        "observed_unix_ms": 1791374000123,
        "kind": kind,
        "before": "5",
        "after": "6",
        "ui_id": "UI-000123",
    }


def rows(path):
    return [
        json.loads(line.split(" INFO ", 1)[1])
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_parallel_streams_preserve_originals_and_restart_without_duplicates(tmp_path):
    mirror = ActivityMirror(tmp_path / "log")
    originals = {}
    for stream in ("native_ram", "semantic_ram"):
        source = tmp_path / f"{stream}.jsonl"
        originals[stream] = [event(i) for i in range(1, 61)]
        source.write_text("".join(json.dumps(e) + "\n" for e in originals[stream]))
        before = source.read_bytes()
        assert mirror.read(stream, source, "a" * 32, "run-1") == 60
        assert source.read_bytes() == before
    parsed = rows(mirror.log)
    assert len(parsed) == 120
    assert len({(r["stream"], r["run_id"], r["sequence"]) for r in parsed}) == 120
    for row in parsed:
        assert row["event"] == originals[row["stream"]][row["sequence"] - 1]
        assert datetime.fromisoformat(row["observed_at"]).utcoffset() is not None
        assert datetime.fromisoformat(row["recorded_at"]).utcoffset() is not None
        assert row["time_basis"] == "observation, not occurrence"
    restarted = ActivityMirror(mirror.directory)
    for stream in originals:
        assert restarted.read(stream, tmp_path / f"{stream}.jsonl", "a" * 32, "run-1") == 0
    assert len(rows(mirror.log)) == 120


def test_partial_source_retry_late_event_and_partial_output_recovery(tmp_path):
    source = tmp_path / "events.jsonl"
    source.write_bytes(json.dumps(event(1)).encode())
    mirror = ActivityMirror(tmp_path / "log")
    assert mirror.read("native_ram", source, "a" * 32, "run-1") == 0
    source.write_bytes(source.read_bytes() + b"\n")
    assert mirror.read("native_ram", source, "a" * 32, "run-1") == 1
    late = event(2, kind="observation_gap")
    late["observed_unix_ms"] -= 10000
    with source.open("a") as output:
        output.write(json.dumps(late) + "\n")
    assert mirror.read("native_ram", source, "a" * 32, "run-1") == 1
    with mirror.log.open("ab") as output:
        output.write(b"unfinished append")
    restarted = ActivityMirror(mirror.directory)
    assert restarted.read("native_ram", source, "a" * 32, "run-1") == 0
    assert rows(mirror.log)[1]["event"] == late


def test_write_failure_does_not_advance_source_or_hide_loss(tmp_path, monkeypatch):
    source = tmp_path / "events.jsonl"
    source.write_text(json.dumps(event(1)) + "\n")
    mirror = ActivityMirror(tmp_path / "log")
    original = type(source).open

    def fail_log(path, *args, **kwargs):
        if path == mirror.log:
            raise PermissionError("Injected write failure")
        return original(path, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(type(source), "open", fail_log)
        with pytest.raises(PermissionError):
            mirror.read("native_ram", source, "a" * 32, "run-1")
    assert mirror.offsets == {} and mirror.seen == set()
    assert mirror.read("native_ram", source, "a" * 32, "run-1") == 1
    assert len(rows(mirror.log)) == 1


def test_wrong_session_and_source_truncation_fail_explicitly(tmp_path):
    source = tmp_path / "events.jsonl"
    source.write_text(json.dumps(event(1)) + "\n")
    mirror = ActivityMirror(tmp_path / "log")
    with pytest.raises(ValueError, match="identity"):
        mirror.read("native_ram", source, "b" * 32, "run-1")
    mirror.read("native_ram", source, "a" * 32, "run-1")
    source.write_bytes(b"")
    with pytest.raises(ValueError, match="truncated"):
        mirror.read("native_ram", source, "a" * 32, "run-1")


def test_worker_live_parallel_lifecycle_and_latency(tmp_path, monkeypatch):
    from cores.hpe990.common.paths import hpe990_folders
    from cores.hpe990.functions import monitoring
    from cores.hpe990.functions.activity_log import run_worker

    session = "a" * 32
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(hpe990_folders, "D_HPE990_RUNTIME", runtime)
    monkeypatch.setattr(hpe990_folders, "D_HPE990_SEMANTIC_RAM", runtime / "semantic-ram")
    monkeypatch.setattr(hpe990_folders, "D_HPE990_ACTIVITY_LOG", runtime / "activity-log")
    running = threading.Event()
    running.set()
    monkeypatch.setattr(monitoring, "_worker_alive", lambda _: running.is_set())
    sources = []
    for name in ("ram", "semantic-ram"):
        directory = runtime / name / session / "run-1"
        directory.mkdir(parents=True)
        (directory.parent / "manifest.json").write_text(
            json.dumps({"directory": str(directory), "worker": {}})
        )
        sources.append(directory / "events.jsonl")
    logger = threading.Thread(target=run_worker, args=(session,))
    logger.start()
    try:
        for i in range(1, 61):
            for source in sources:
                row = event(
                    i,
                    kind=(
                        "value_changed",
                        "text_changed",
                        "pixel_changed",
                        "window_opened",
                        "window_closed",
                        "observation_gap",
                    )[i % 6],
                )
                row["observed_unix_ms"] = time.time_ns() // 1000000
                with source.open("a") as output:
                    output.write(json.dumps(row) + "\n")
            time.sleep(0.002)
        log = runtime / "activity-log" / session / "activity.log"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if log.exists() and len(rows(log)) == 120:
                break
            time.sleep(0.02)
        parsed = rows(log)
        assert len(parsed) == 120 and logger.is_alive()
        delays = sorted(r["recorded_unix_ms"] - r["observed_unix_ms"] for r in parsed)
        assert delays[int(len(delays) * 0.99)] < 1000
    finally:
        running.clear()
        logger.join(timeout=5)
    assert not logger.is_alive()
    status = json.loads((log.parent / "status.json").read_text())
    assert not status["active"] and status["errors"] == 0
    assert status["records"] == 120


def test_status_replacement_retries_windows_reader_lock(tmp_path, monkeypatch):
    from cores.hpe990.functions.activity_log import _write_status

    original = type(tmp_path).replace
    failures = []

    def temporarily_locked(path, destination):
        if len(failures) < 2:
            failures.append(True)
            raise PermissionError("Reader owns the Windows file handle")
        return original(path, destination)

    monkeypatch.setattr(type(tmp_path), "replace", temporarily_locked)
    _write_status(tmp_path, {"active": True})
    assert json.loads((tmp_path / "status.json").read_text()) == {"active": True}

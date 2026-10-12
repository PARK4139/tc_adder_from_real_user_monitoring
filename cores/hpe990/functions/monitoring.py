"""Session-scoped RAM worker control and evidence access."""

import json
import time
import uuid
from pathlib import Path

import psutil
from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.backend import request_backend
from cores.hpe990.functions.lifecycle import _alive, _read_session, log_event


def session_guard(session_id: str, require_running: bool = True) -> dict:
    session = _read_session()
    if not session or session["session_id"] != session_id:
        raise ValueError("Unknown or stale session_id")
    if require_running and not any(_alive(p) for p in session["processes"]):
        raise ValueError("Session process is no longer running")
    return session


def _manifest_path(session_id: str) -> Path:
    session_guard(session_id, False)
    return hpe990_folders.D_HPE990_RUNTIME / "ram" / session_id / "manifest.json"


def _worker_alive(record: dict) -> bool:
    try:
        process = psutil.Process(record["pid"])
        return process.is_running() and process.create_time() == record["create_time"]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def ram_status(session_id: str) -> dict:
    path = _manifest_path(session_id)
    if not path.is_file():
        return {"session_id": session_id, "active": False}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    directory = Path(manifest["directory"])
    result = {**manifest, "active": _worker_alive(manifest["worker"])}
    from cores.hpe990.functions.activity_log import activity_status

    try:
        result["activity_log"] = activity_status(session_id)
    except (OSError, ValueError, KeyError) as error:
        result["activity_log"] = {"active": False, "error": str(error)}
    for name in ("snapshot", "ram-report"):
        source = directory / f"{name}.json"
        for _ in range(10):
            try:
                if source.exists():
                    result[name.replace("-", "_")] = json.loads(source.read_text(encoding="utf-8"))
                break
            except (FileNotFoundError, PermissionError, json.JSONDecodeError):
                time.sleep(0.01)
    return result


def start_ram(session_id: str, interval_ms: int = 100) -> dict:
    if isinstance(interval_ms, bool) or not 20 <= interval_ms <= 1000:
        raise ValueError("interval_ms must be between 20 and 1000")
    session = session_guard(session_id)
    path = _manifest_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path) + ".lock", timeout=30):
        existing = ram_status(session_id)
        if existing["active"]:
            from cores.hpe990.functions.activity_log import ensure_activity_log

            existing["activity_log"] = ensure_activity_log(session_id)
            return existing
        if len(session["processes"]) != 1:
            raise ValueError("RAM currently requires exactly one live target process")
        process = session["processes"][0]
        directory = path.parent / uuid.uuid4().hex
        directory.mkdir()
        worker = request_backend(
            "ram",
            {
                **process,
                "directory": str(directory),
                "session_id": session_id,
                "interval_ms": interval_ms,
            },
        )
        manifest = {
            "session_id": session_id,
            "directory": str(directory),
            "worker": worker,
            "interval_ms": interval_ms,
            "target": process,
        }
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        with (path.parent / "runs.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(manifest) + "\n")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            status = ram_status(session_id)
            if status.get("snapshot"):
                from cores.hpe990.functions.activity_log import ensure_activity_log

                status["activity_log"] = ensure_activity_log(session_id)
                log_event("ram_started", session_id=session_id, directory=str(directory))
                return status
            if not status["active"]:
                raise RuntimeError(f"RAM worker exited: {directory / 'worker-stderr.log'}")
            time.sleep(0.05)
        raise TimeoutError("RAM first snapshot missing")


def stop_ram(session_id: str) -> dict:
    status = ram_status(session_id)
    if not status["active"]:
        return status
    (Path(status["directory"]) / "stop.request").touch()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        status = ram_status(session_id)
        if not status["active"] and status.get("ram_report"):
            log_event("ram_stopped", session_id=session_id, directory=status["directory"])
            return status
        time.sleep(0.05)
    raise TimeoutError("RAM worker did not stop or finalize evidence")


def telemetry_read(session_id: str, after_sequence: int = 0, limit: int = 200) -> dict:
    if after_sequence < 0 or not 1 <= limit <= 10000:
        raise ValueError("Invalid sequence cursor or limit")
    status = ram_status(session_id)
    if "directory" not in status:
        raise ValueError("Start RAM before reading telemetry")
    events = []
    source = Path(status["directory"]) / "events.jsonl"
    with source.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                break  # Concurrent writer's incomplete final line is retried on the next read.
            if record["sequence"] > after_sequence:
                events.append(record)
                if len(events) == limit:
                    break
    return {
        "session_id": session_id,
        "events": events,
        "run_id": Path(status["directory"]).name,
        "next_sequence": events[-1]["sequence"] if events else after_sequence,
        "source": str(source),
        "active": status["active"],
    }


def action_marker(session_id: str, action_id: str, phase: str, details: dict) -> None:
    status = ram_status(session_id)
    if not status["active"]:
        raise RuntimeError("RAM must be active before controlling UI")
    commands = Path(status["directory"]) / "commands"
    commands.mkdir(exist_ok=True)
    pending = commands / f"{uuid.uuid4().hex}.pending"
    record = {
        "kind": "control_action",
        "session_id": session_id,
        "action_id": action_id,
        "phase": phase,
        "submitted_unix_ms": time.time_ns() // 1000000,
        **details,
    }
    pending.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    submitted = pending.with_suffix(".json")
    pending.replace(submitted)
    receipt = Path(status["directory"]) / "processed-commands" / submitted.name
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if receipt.is_file():
            return
        if not _worker_alive(status["worker"]):
            raise RuntimeError("RAM worker exited before recording action marker")
        time.sleep(0.01)
    raise TimeoutError("RAM action marker acknowledgement missing")


def telemetry_export(session_id: str) -> dict:
    status = ram_status(session_id)
    if "directory" not in status:
        raise ValueError("No RAM evidence for this session")
    directory = Path(status["directory"])
    run_id = directory.name
    rows = []
    sequence = 0
    while True:
        page = telemetry_read(session_id, sequence, 10000)
        rows.extend(page["events"])
        if not page["events"]:
            break
        sequence = page["next_sequence"]
    failures = []
    for index, row in enumerate(rows, 1):
        if not (
            row.get("schema_version") == 1
            and row.get("sequence") == index
            and row.get("session_id") == session_id
            and row.get("run_id") == run_id
            and isinstance(row.get("observed_unix_ms"), int)
            and isinstance(row.get("kind"), str)
        ):
            failures.append(index)
    from collections import Counter

    destination = hpe990_folders.D_HPE990_EVIDENCE / "4c1abd34" / run_id
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "events.jsonl"
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    report = {
        "schema_version": 1,
        "session_id": session_id,
        "run_id": run_id,
        "events": len(rows),
        "schema_errors": failures,
        "sequence_duplicates": len(rows) - len({r["sequence"] for r in rows}),
        "event_kinds": dict(Counter(r["kind"] for r in rows)),
        "native_categories": dict(Counter(r["category"] for r in rows if "category" in r)),
        "source": str(directory / "events.jsonl"),
        "export": str(output),
        "active": status["active"],
        "ram_report": status.get("ram_report"),
        "transport": "local JSONL only",
        "verdict": "PASS" if rows and not failures else "FAIL",
    }
    report["evidence"] = str(destination / "telemetry-report.json")
    Path(report["evidence"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

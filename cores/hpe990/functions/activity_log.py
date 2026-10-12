"""Independent, restartable human-readable mirror of original RAM event streams."""

import json
import os
import re
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders


def _directory(session_id):
    if not re.fullmatch(r"[0-9a-f]{32}", session_id):
        raise ValueError("Invalid session identity")
    return hpe990_folders.D_HPE990_ACTIVITY_LOG / session_id


def _write_status(directory, data):
    pending = directory / "status.pending"
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    deadline = time.monotonic() + 1
    while True:
        try:
            pending.replace(directory / "status.json")
            break
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def activity_status(session_id):
    from cores.hpe990.functions.monitoring import _worker_alive

    directory = _directory(session_id)
    path = directory / "manifest.json"
    if not path.exists():
        return {"active": False, "log": str(directory / "activity.log")}
    result = json.loads(path.read_text(encoding="utf-8"))
    result["active"] = _worker_alive(result["worker"])
    status = directory / "status.json"
    if status.exists():
        result["writer"] = json.loads(status.read_text(encoding="utf-8"))
    return result


def ensure_activity_log(session_id):
    """RAM start attaches the logger; failure never terminates a collector."""
    from cores.hpe990.functions.backend import request_backend

    directory = _directory(session_id)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(str(directory / "start.lock"), timeout=5):
            result = activity_status(session_id)
            if result["active"]:
                return result
            worker = request_backend("activity_log", {"session_id": session_id})
            record = {
                "session_id": session_id,
                "worker": worker,
                "log": str(directory / "activity.log"),
            }
            (directory / "manifest.json").write_text(json.dumps(record), encoding="utf-8")
            return activity_status(session_id)
    except Exception as error:
        return {
            "active": False,
            "error": f"{type(error).__name__}: {error}",
            "log": str(directory / "activity.log"),
        }


class ActivityMirror:
    """Read complete source lines only; recover deduplication from durable output."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.log = self.directory / "activity.log"
        self.seen = set()
        self.offsets = {}
        self.available_at = {}
        self.delays_ms = deque(maxlen=10000)
        self.errors = 0
        if self.log.exists():
            # A failed append may leave one incomplete last line. Retain complete records.
            with self.log.open("r+b") as stream:
                while True:
                    start = stream.tell()
                    line = stream.readline()
                    if not line:
                        break
                    if not line.endswith(b"\n"):
                        stream.truncate(start)
                        break
                    record = json.loads(line.decode("utf-8").split(" INFO ", 1)[1])
                    self.seen.add((record["stream"], record["run_id"], record["sequence"]))

    def read(self, stream_name, source, session_id, run_id):
        source = Path(source)
        if not source.exists():
            return 0
        offset = self.offsets.get(str(source), 0)
        if source.stat().st_size < offset:
            raise ValueError(f"Source was truncated: {source}")
        count = 0
        pending = []
        identities = set()
        consumed = []
        end = offset
        available_batch = time.time_ns() // 1000000
        with source.open("rb") as input_stream:
            input_stream.seek(offset)
            while True:
                start = input_stream.tell()
                line = input_stream.readline()
                if not line or not line.endswith(b"\n"):
                    break
                key = (str(source), start)
                available = self.available_at.setdefault(key, available_batch)
                event = json.loads(line)
                if (
                    event.get("session_id") != session_id
                    or event.get("run_id") != run_id
                    or type(event.get("sequence")) is not int
                    or event["sequence"] < 1
                    or type(event.get("observed_unix_ms")) is not int
                ):
                    raise ValueError(f"Invalid source identity or timestamp: {source}:{start}")
                identity = (stream_name, run_id, event["sequence"])
                if identity not in self.seen and identity not in identities:
                    recorded = time.time_ns() // 1000000
                    observed_at = (
                        datetime.fromtimestamp(event["observed_unix_ms"] / 1000)
                        .astimezone()
                        .isoformat(timespec="milliseconds")
                    )
                    recorded_at = (
                        datetime.fromtimestamp(recorded / 1000)
                        .astimezone()
                        .isoformat(timespec="milliseconds")
                    )
                    record = {
                        "stream": stream_name,
                        "session_id": session_id,
                        "run_id": run_id,
                        "sequence": event["sequence"],
                        "ui_id": event.get("ui_id", "unidentified"),
                        "kind": event["kind"],
                        "time_basis": "observation, not occurrence",
                        "observed_at": observed_at,
                        "observed_unix_ms": event["observed_unix_ms"],
                        "recorded_at": recorded_at,
                        "recorded_unix_ms": recorded,
                        "available_unix_ms": available,
                        "source": str(source),
                        "source_offset": start,
                        "event": event,
                    }
                    pending.append(
                        (
                            observed_at + " INFO " + json.dumps(record, ensure_ascii=False) + "\n",
                            available,
                        )
                    )
                    identities.add(identity)
                    count += 1
                end = input_stream.tell()
                consumed.append(key)
                if len(consumed) >= 1000:
                    break
        if pending:
            with self.log.open("ab") as output:
                previous_size = output.tell()
                try:
                    output.write("".join(line for line, _ in pending).encode("utf-8"))
                    output.flush()
                    os.fsync(output.fileno())
                except OSError:
                    output.seek(previous_size)
                    output.truncate()
                    raise
            completed = time.time_ns() // 1000000
            self.seen.update(identities)
            self.delays_ms.extend(completed - available for _, available in pending)
        if consumed:
            self.offsets[str(source)] = end
            for key in consumed:
                self.available_at.pop(key, None)
        return count

    def report(self):
        delays = sorted(self.delays_ms)
        return {
            "records": len(self.seen),
            "errors": self.errors,
            "available_to_append_p99_ms": delays[min(len(delays) - 1, int(len(delays) * 0.99))]
            if delays
            else None,
            "offsets": self.offsets,
            "log": str(self.log),
        }


def run_worker(session_id):
    from cores.hpe990.functions.monitoring import _worker_alive

    directory = _directory(session_id)
    sources = {}
    with FileLock(str(directory / "writer.lock"), timeout=0):
        mirror = ActivityMirror(directory)
        while True:
            active = False
            errors = []
            for name, base in (
                ("native_ram", hpe990_folders.D_HPE990_RUNTIME / "ram"),
                ("semantic_ram", hpe990_folders.D_HPE990_SEMANTIC_RAM),
            ):
                manifest = base / session_id / "manifest.json"
                try:
                    if manifest.exists():
                        record = json.loads(manifest.read_text(encoding="utf-8"))
                        run = Path(record["directory"])
                        sources[(name, run.name)] = run / "events.jsonl"
                        active |= _worker_alive(record["worker"])
                except (OSError, json.JSONDecodeError) as error:
                    errors.append(f"Manifest read failed: {manifest}: {error}")
                    active = True  # Retry a transient read rather than silently ending logging.
            for (name, run_id), path in sources.items():
                try:
                    mirror.read(name, path, session_id, run_id)
                except (OSError, ValueError, KeyError) as error:
                    mirror.errors += 1
                    errors.append(f"{name}/{run_id}: {error}")
            _write_status(
                directory,
                {
                    **mirror.report(),
                    "active": active,
                    "updated_unix_ms": time.time_ns() // 1000000,
                    "current_errors": errors,
                },
            )
            drained = all(
                not path.exists() or path.stat().st_size == mirror.offsets.get(str(path), 0)
                for path in sources.values()
            )
            if not active and not drained and not errors:
                # A collector exited with an incomplete final line; do not report a clean drain.
                incomplete = [
                    str(path)
                    for path in sources.values()
                    if path.exists()
                    and path.stat().st_size > mirror.offsets.get(str(path), 0)
                    and path.read_bytes()[-1:] != b"\n"
                ]
                if incomplete:
                    mirror.errors += 1
                    errors.append(
                        "Observation gap: incomplete final source line: " + ", ".join(incomplete)
                    )
                    _write_status(
                        directory, {**mirror.report(), "active": False, "current_errors": errors}
                    )
            if not active and (drained or errors):
                break
            time.sleep(0.1)


if __name__ == "__main__":
    run_worker(sys.argv[1])

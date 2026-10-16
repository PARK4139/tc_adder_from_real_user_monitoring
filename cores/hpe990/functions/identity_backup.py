"""Bounded canonical ID snapshots; historical observations stay in the source."""

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.identity_database import open_identity_database
from cores.hpe990.functions.monitoring import ram_status, session_guard

AUTHORITY_TABLES = ("elements", "ui_map_targets", "ui_map_bindings")
SCOPE = (
    "Canonical UI definitions, allocator counters and semantic mappings only. "
    "Historical observations, session aliases, Real Activity Monitoring logs and screenshots remain in the source; "
    "this is not a complete historical backup."
)


def snapshot_identity_authority(source_path: Path, destination: Path, timeout_seconds=60) -> dict:
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int):
        raise ValueError("timeout_seconds must be an integer in 1..300")
    if not 1 <= timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be in 1..300")
    source_path, destination = Path(source_path).resolve(), Path(destination).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    pending = destination.with_suffix(destination.suffix + ".partial")
    if destination.exists() or pending.exists():
        raise FileExistsError(destination)
    started = time.monotonic()
    deadline = started + timeout_seconds

    def expired():
        return time.monotonic() >= deadline

    def check():
        if expired():
            raise TimeoutError("Canonical snapshot deadline exceeded; no backup published")

    # Readers no longer prevent live ID writers from committing.
    with closing(open_identity_database(source_path)):
        check()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(
            sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True, timeout=1)
        ) as source:
            with closing(sqlite3.connect(pending, timeout=1)) as target:
                source.set_progress_handler(expired, 1000)
                target.set_progress_handler(expired, 1000)
                source.execute("BEGIN")
                schemas = source.execute(
                    "SELECT name,sql FROM sqlite_master WHERE type='table' AND name!='sqlite_sequence'"
                ).fetchall()
                for _, sql in schemas:
                    check()
                    target.execute(sql)
                target.execute("BEGIN")
                tables = {name for name, _ in schemas}
                rows = {}
                for name in AUTHORITY_TABLES:
                    if name not in tables:
                        continue
                    cursor = source.execute(f'SELECT * FROM "{name}"')
                    insert = (
                        f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in cursor.description)})'
                    )
                    rows[name] = 0
                    while batch := cursor.fetchmany(256):
                        check()
                        target.executemany(insert, batch)
                        rows[name] += len(batch)
                counters = source.execute(
                    "SELECT name,seq FROM sqlite_sequence ORDER BY name"
                ).fetchall()
                target.execute("DELETE FROM sqlite_sequence")
                target.executemany("INSERT INTO sqlite_sequence VALUES (?,?)", counters)
                source.rollback()
                read_ms = round((time.monotonic() - started) * 1000, 3)
                target.commit()
                integrity = target.execute("PRAGMA integrity_check").fetchall()
                foreign_keys = target.execute("PRAGMA foreign_key_check").fetchall()
                copied = target.execute(
                    "SELECT name,seq FROM sqlite_sequence ORDER BY name"
                ).fetchall()
                if integrity != [("ok",)] or foreign_keys or counters != copied:
                    raise RuntimeError("Canonical snapshot failed integrity/counter verification")
        digest = hashlib.sha256()
        with pending.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                check()
                digest.update(chunk)
        check()
        # Caller gives a new UUID directory; never replace an existing backup.
        if destination.exists():
            raise FileExistsError(destination)
        pending.rename(destination)
        return {
            "completed": True,
            "scope": SCOPE,
            "path": str(destination),
            "rows": rows,
            "counters": counters,
            "bytes": destination.stat().st_size,
            "sha256": digest.hexdigest(),
            "integrity_check": "ok",
            "foreign_key_errors": [],
            "source_read_transaction_ms": read_ms,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
        }
    except BaseException as error:
        # Both connections have closed before removing only this new temporary file.
        pending.unlink(missing_ok=True)
        pending.with_name(pending.name + "-journal").unlink(missing_ok=True)
        if isinstance(error, sqlite3.OperationalError) and expired():
            raise TimeoutError(
                "Canonical snapshot deadline exceeded; no backup published"
            ) from error
        raise


def backup_identity_authority(session_id: str, timeout_seconds: int = 60) -> dict:
    session_guard(session_id)
    if not ram_status(session_id)["active"]:
        raise RuntimeError(
            "Native Real Activity Monitoring must remain active during registry backup"
        )
    directory = hpe990_folders.D_HPE990_EVIDENCE / "ffba3c51" / session_id / uuid.uuid4().hex
    with FileLock(str(hpe990_folders.D_HPE990_RUNTIME / "identity-backup.lock"), timeout=0.1):
        result = snapshot_identity_authority(
            hpe990_folders.F_HPE990_UI_REGISTRY,
            directory / "identity-authority.sqlite3",
            timeout_seconds,
        )
        result["session_id"] = session_id
        result["native_ram_active_after"] = ram_status(session_id)["active"]
        (directory / "manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

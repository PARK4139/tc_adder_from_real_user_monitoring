"""Reader/writer isolation, canonical snapshot integrity and failure cleanup."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest

from cores.hpe990.functions import identity_backup
from cores.hpe990.functions.identity_backup import snapshot_identity_authority
from cores.hpe990.functions.ui_identity import assign_ui_ids
from cores.hpe990.functions.ui_mapping import connect
from cores.hpe990.tests.test_ui_identity import snapshot


def test_delete_reader_blocks_writer_commit(tmp_path):
    path = tmp_path / "delete.sqlite3"
    with closing(sqlite3.connect(path, timeout=0.02)) as writer:
        writer.execute("CREATE TABLE value(n)")
        writer.execute("INSERT INTO value VALUES (1)")
        writer.commit()
        with closing(sqlite3.connect(path)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT * FROM value").fetchall()
            writer.execute("UPDATE value SET n=2")
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                writer.commit()
        writer.commit()
        assert writer.execute("SELECT n FROM value").fetchone() == (2,)


@pytest.mark.parametrize("trial", range(3))
def test_wal_reader_allows_identity_writer(tmp_path, trial):
    path = tmp_path / "wal.sqlite3"
    first = snapshot()
    assign_ui_ids(first, path)
    with closing(sqlite3.connect(path)) as reader:
        reader.execute("BEGIN")
        previous = reader.execute("SELECT count(*) FROM observations").fetchone()[0]
        with ThreadPoolExecutor(max_workers=1) as pool:
            next_record = snapshot(evidence=f"next-{trial}")
            pool.submit(assign_ui_ids, next_record, path).result(timeout=2)
        assert next_record["nodes"][0]["ui_id"] == first["nodes"][0]["ui_id"]
        assert reader.execute("SELECT count(*) FROM observations").fetchone()[0] == previous
    with closing(sqlite3.connect(path)) as reader:
        assert reader.execute("SELECT count(*) FROM observations").fetchone()[0] == previous * 2


def test_authority_snapshot_preserves_ids_maps_counters_not_history(tmp_path):
    source, target = tmp_path / "source.sqlite3", tmp_path / "snapshot.sqlite3"
    assign_ui_ids(snapshot(), source)
    with closing(connect(source)) as db, db:
        db.execute("INSERT INTO ui_map_targets VALUES (?,?)", ("HPE990:version-one", "{}"))
        db.execute(
            "INSERT INTO ui_map_bindings VALUES (?,?,?,?,?,?,?)",
            ("HPE990:version-one", "HPE990.Preferences", "{}", "[]", "one", "UI-000001", 123),
        )
    result = snapshot_identity_authority(source, target)
    assert result["completed"] and result["integrity_check"] == "ok"
    assert result["foreign_key_errors"] == []
    with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(target)) as backup:
        for table in identity_backup.AUTHORITY_TABLES:
            assert (
                original.execute(f"SELECT * FROM {table}").fetchall()
                == backup.execute(f"SELECT * FROM {table}").fetchall()
            )
        assert backup.execute("SELECT count(*) FROM observations").fetchone() == (0,)
        assert (
            backup.execute("SELECT * FROM sqlite_sequence").fetchall()
            == original.execute("SELECT * FROM sqlite_sequence").fetchall()
        )
    with pytest.raises(FileExistsError):
        snapshot_identity_authority(source, target)


def test_deadline_releases_reader_and_never_publishes(tmp_path, monkeypatch):
    source, target = tmp_path / "source.sqlite3", tmp_path / "snapshot.sqlite3"
    assign_ui_ids(snapshot(), source)
    clock = iter([0, 0, 0, 2])
    monkeypatch.setattr(identity_backup.time, "monotonic", lambda: next(clock, 2))
    with pytest.raises(TimeoutError):
        snapshot_identity_authority(source, target, timeout_seconds=1)
    assert not target.exists()
    assert not target.with_suffix(".sqlite3.partial").exists()
    assign_ui_ids(snapshot(evidence="after-failure"), source)


def test_interrupt_cleans_pending_and_releases_connections(tmp_path, monkeypatch):
    source, target = tmp_path / "source.sqlite3", tmp_path / "snapshot.sqlite3"
    assign_ui_ids(snapshot(), source)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(identity_backup.hashlib, "sha256", interrupted)
    with pytest.raises(KeyboardInterrupt):
        snapshot_identity_authority(source, target)
    assert not target.exists() and not target.with_suffix(".sqlite3.partial").exists()
    assign_ui_ids(snapshot(evidence="after-interruption"), source)

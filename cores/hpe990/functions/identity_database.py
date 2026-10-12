"""SQLite engine configuration for concurrent identity writers and evidence readers."""

import sqlite3
from pathlib import Path


def open_identity_database(database: Path, timeout: float = 1.0) -> sqlite3.Connection:
    """Require WAL before writes; never silently use a blocking rollback journal.

    Python orchestrates the native SQLite engine. Callers close the connection.
    Busy transitions fail within the connection timeout; IDs are never recreated.
    """
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=timeout)
    try:
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        if mode != "wal":
            mode = connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        if mode != "wal":
            raise RuntimeError(f"Identity registry requires WAL, got {mode}")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
    except BaseException:
        connection.close()
        raise

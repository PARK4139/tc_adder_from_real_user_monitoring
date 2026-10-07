"""Actual Windows reader sharing must not kill the status writer."""

import json
import sys
import threading
import time

import pytest

from cores.hpe990.functions.semantic_ram import _write


@pytest.mark.skipif(sys.platform != "win32", reason="Windows sharing behavior")
@pytest.mark.parametrize("attempt", range(3))
def test_status_replace_waits_for_reader_and_keeps_complete_json(tmp_path, attempt):
    path = tmp_path / "status.json"
    _write(path, {"sequence": attempt})
    reader = path.open(encoding="utf-8")
    result = []

    def write():
        try:
            _write(path, {"sequence": attempt + 1})
            result.append("ok")
        except Exception as error:
            result.append(error)

    worker = threading.Thread(target=write)
    worker.start()
    try:
        time.sleep(0.08)
        assert json.load(reader) == {"sequence": attempt}
        assert worker.is_alive()
    finally:
        reader.close()
        worker.join(timeout=2)
    assert result == ["ok"]
    assert json.loads(path.read_text(encoding="utf-8")) == {"sequence": attempt + 1}


def test_permanent_permission_error_is_bounded_and_preserves_previous_json(tmp_path, monkeypatch):
    from pathlib import Path

    from cores.hpe990.functions import semantic_ram

    path = tmp_path / "status.json"
    _write(path, {"sequence": 1})
    times = iter([0, 2])
    monkeypatch.setattr(semantic_ram.time, "monotonic", lambda: next(times))

    def denied(*args):
        raise PermissionError("Permanent refusal")

    monkeypatch.setattr(Path, "replace", denied)
    with pytest.raises(PermissionError):
        _write(path, {"sequence": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"sequence": 1}


def test_unrelated_errors_are_not_retried(tmp_path, monkeypatch):
    from pathlib import Path

    attempts = []

    def failed(*args):
        attempts.append(1)
        raise OSError("Non-sharing error")

    monkeypatch.setattr(Path, "replace", failed)
    with pytest.raises(OSError, match="Non-sharing"):
        _write(tmp_path / "status.json", {"sequence": 1})
    assert attempts == [1]

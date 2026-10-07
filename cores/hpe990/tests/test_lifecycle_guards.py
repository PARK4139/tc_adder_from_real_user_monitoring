import math

import pytest

from cores.hpe990.functions import lifecycle


@pytest.mark.parametrize("value", [0, -1, 121, math.inf, math.nan, True])
def test_invalid_timeout_cannot_start_an_application(value):
    with pytest.raises(ValueError):
        lifecycle.launch_emulator(value)


def test_pid_reuse_is_not_a_live_owned_process(monkeypatch):
    class ReusedProcess:
        def __init__(self, pid):
            self.pid = pid

        def is_running(self):
            return True

        def create_time(self):
            return 999

    monkeypatch.setattr(lifecycle.psutil, "Process", ReusedProcess)
    assert not lifecycle._alive({"pid": 42, "create_time": 123, "exe": "old.exe"})


def test_cannot_close_an_external_session(monkeypatch, tmp_path):
    monkeypatch.setattr(lifecycle, "F_HPE990_LOCK", tmp_path / "lifecycle.lock")
    monkeypatch.setattr(
        lifecycle, "_read_session", lambda: {"session_id": "external", "owned": False}
    )
    with pytest.raises(PermissionError, match="externally started"):
        lifecycle.close_emulator("external", 0.1)


def test_cannot_close_a_stale_session(monkeypatch, tmp_path):
    monkeypatch.setattr(lifecycle, "F_HPE990_LOCK", tmp_path / "lifecycle.lock")
    monkeypatch.setattr(
        lifecycle, "_read_session", lambda: {"session_id": "current", "owned": True}
    )
    with pytest.raises(ValueError, match="stale"):
        lifecycle.close_emulator("old", 0.1)


@pytest.mark.parametrize("force", [False, True])
def test_explicit_stop_cannot_terminate_an_external_session(monkeypatch, tmp_path, force):
    monkeypatch.setattr(lifecycle, "F_HPE990_LOCK", tmp_path / "lifecycle.lock")
    monkeypatch.setattr(
        lifecycle, "_read_session", lambda: {"session_id": "external", "owned": False}
    )
    with pytest.raises(PermissionError, match="externally started"):
        lifecycle.stop_session("external", force, 0.1)


def test_trial_dialog_is_not_launch_completion(monkeypatch):
    monkeypatch.setattr(lifecycle, "_alive", lambda record: True)
    monkeypatch.setattr(lifecycle, "_windows", lambda records: [{"title": "PC Simulator"}])
    status = lifecycle._status({"processes": [{"pid": 1}], "session_id": "trial"})
    assert status["running"] and not status["ready"]
    assert not status["startup_completed"]


def test_edger_is_verified_launch_completion(monkeypatch):
    monkeypatch.setattr(lifecycle, "_alive", lambda record: True)
    monkeypatch.setattr(lifecycle, "_windows", lambda records: [{"title": "Edger"}])
    status = lifecycle._status({"processes": [{"pid": 1}], "session_id": "edger"})
    assert status["ready"] and status["startup_completed"]

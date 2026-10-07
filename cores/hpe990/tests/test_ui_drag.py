"""Reject unsafe drag targets/parameters and release a pressed button after worker timeout."""

import json
import subprocess
from copy import deepcopy

import pytest

from cores.hpe990.functions import ui_drag


def inventory():
    root = {
        "hwnd": 1,
        "ui_id": "UI-000001",
        "parent": 0,
        "visible": True,
        "enabled": True,
        "pid": 10,
        "name": "Preferences",
        "class_name": "QWidget",
        "rect": [0, 0, 100, 100],
    }
    child = root | {"hwnd": 2, "ui_id": "UI-000002", "parent": 1, "name": "bar"}
    return {"nodes": [root, child], "evidence": "snapshot.json"}


@pytest.mark.parametrize(
    "start,end,duration",
    [
        ([0, 0.5], [0.5, 0.5], 500),
        ([True, 0.5], [0.5, 0.5], 500),
        ([float("nan"), 0.5], [0.5, 0.5], 500),
        ([0.5], [0.5, 0.5], 500),
        ([0.5, 0.5], [0.5, float("inf")], 500),
        ([0.5, 0.5], [0.5, 0.6], True),
        ([0.5, 0.5], [0.5, 0.6], 49),
        ([0.5, 0.5], [0.5, 0.6], 5001),
    ],
)
def test_invalid_drag_arguments_fail_before_session_or_input(start, end, duration, monkeypatch):
    monkeypatch.setattr(ui_drag, "session_guard", lambda *args: pytest.fail("Session accessed"))
    with pytest.raises(ValueError):
        ui_drag.drag_ui("unused", "UI-000002", start, end, duration_ms=duration)


def test_disabled_ancestor_and_ambiguous_ids_are_rejected():
    record = inventory()
    record["nodes"][0]["enabled"] = False
    with pytest.raises(ValueError, match="ancestor"):
        ui_drag.resolve_drag_node(record, "UI-000002")
    record = inventory()
    record["nodes"].append(deepcopy(record["nodes"][1]))
    with pytest.raises(ValueError, match="one currently"):
        ui_drag.resolve_drag_node(record, "UI-000002")


def test_unknown_or_ocr_only_id_is_not_native_target():
    record = inventory()
    record["visual"] = {"elements": [{"ui_id": "UI-000003"}]}
    with pytest.raises(ValueError):
        ui_drag.resolve_drag_node(record, "UI-000003")


def test_endpoint_clipped_by_parent_is_rejected(monkeypatch):
    record = inventory()
    monkeypatch.setattr(ui_drag.win32gui, "ClientToScreen", lambda hwnd, point: point)
    record["nodes"][0]["rect"] = [0, 0, 100, 50]
    with pytest.raises(ValueError, match="ancestor bounds"):
        ui_drag._check_visible_point(record, record["nodes"][1], [50, 75])


@pytest.mark.parametrize("worker_timed_out", [True, False])
def test_worker_receipt_controls_timeout_cleanup(tmp_path, monkeypatch, worker_timed_out):
    record = inventory()
    folders = deepcopy(ui_drag.hpe990_folders)
    folders.D_HPE990_RUNTIME = tmp_path
    folders.D_HPE990_EVIDENCE = tmp_path
    folders.F_HPE990_INPUT = tmp_path / "input.exe"
    folders.F_HPE990_INPUT.touch()
    monkeypatch.setattr(ui_drag, "hpe990_folders", folders)
    monkeypatch.setattr(ui_drag, "session_guard", lambda *_: {})
    monkeypatch.setattr(ui_drag, "start_ram", lambda *_: {"directory": "ram"})
    monkeypatch.setattr(ui_drag, "ram_status", lambda *_: {"active": True})
    monkeypatch.setattr(ui_drag, "collect_ui", lambda *a, **k: record)
    monkeypatch.setattr(ui_drag, "_native_tree", lambda *_: record["nodes"])
    monkeypatch.setattr(ui_drag, "_point", lambda _, p: [int(p[0] * 100), int(p[1] * 100)])
    monkeypatch.setattr(ui_drag.win32gui, "ClientToScreen", lambda _, p: p)
    monkeypatch.setattr(ui_drag.win32gui, "ScreenToClient", lambda _, p: p)
    monkeypatch.setattr(ui_drag.win32gui, "IsWindow", lambda _: True)
    monkeypatch.setattr(ui_drag.win32process, "GetWindowThreadProcessId", lambda _: (1, 10))
    monkeypatch.setattr(ui_drag.time, "sleep", lambda _: None)
    released, phases = [], []
    monkeypatch.setattr(ui_drag.win32gui, "PostMessage", lambda *a: released.append(a))
    monkeypatch.setattr(ui_drag, "action_marker", lambda s, a, phase, details: phases.append(phase))

    def timeout(*a, **k):
        if worker_timed_out:
            raise subprocess.TimeoutExpired(a[0], k["timeout"])
        return subprocess.CompletedProcess(
            a[0], 0, json.dumps({"ok": True, "button_release_posted": True}).encode()
        )

    monkeypatch.setattr(ui_drag.subprocess, "run", timeout)
    if worker_timed_out:
        with pytest.raises(subprocess.TimeoutExpired):
            ui_drag.drag_ui("session", "UI-000002", [0.5, 0.3], [0.5, 0.6])
        assert released[0][:3] == (2, ui_drag.win32con.WM_LBUTTONUP, 0)
        assert phases == ["requested", "failed"]
    else:
        result = ui_drag.drag_ui("session", "UI-000002", [0.5, 0.3], [0.5, 0.6])
        assert not released
        assert phases == ["requested", "observed"]
        assert result["ram_active"]
    assert list(tmp_path.rglob("receipt.json"))

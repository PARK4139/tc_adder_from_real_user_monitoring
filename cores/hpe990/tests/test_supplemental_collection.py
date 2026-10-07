"""Verify evidence association and failure isolation without desktop input."""

import subprocess

import pytest

from cores.hpe990.functions.accessibility import collect_accessibility
from cores.hpe990.functions.ui import _associate_visual_nodes
from cores.hpe990.functions.visual_elements import collect_visual_elements, link_frames


def test_frame_label_and_text_do_not_claim_semantic_value():
    lines = [
        {"text": "Group heading", "rect": [10, 10, 150, 22]},
        {"text": "Backup Date", "rect": [10, 35, 90, 47]},
        {"text": "2026-10-07", "rect": [205, 35, 270, 47]},
        {"text": "Other field", "rect": [10, 75, 90, 87]},
    ]
    field = link_frames(lines, [[200, 30, 350, 60]])[0]
    assert field["name"] == "Backup Date"
    assert field["observed_text"] == "2026-10-07"
    assert field["value"] is None
    assert field["readonly"] is None
    assert field["enabled"] is None


def test_unlabeled_frame_does_not_invent_name():
    assert link_frames([], [[200, 30, 350, 60]])[0]["name"] is None


def test_provider_timeout_is_structured_and_bounded(monkeypatch):
    def stalled(*args, **kwargs):
        assert kwargs["timeout"] == 3
        assert kwargs["stdin"] == subprocess.DEVNULL
        raise subprocess.TimeoutExpired(args[0], 3)

    monkeypatch.setattr(subprocess, "run", stalled)
    roots = [{"hwnd": 1, "pid": 123, "visible": True, "enabled": True, "class_name": "QWidget"}]
    result = collect_accessibility(roots)
    assert result["elements"] == []
    assert result["errors"] == ["Provider timed out after 3s"]
    assert result["complete"] is False


def test_invalid_backend_fails_and_no_screenshot_skips_ocr():
    with pytest.raises(ValueError):
        collect_accessibility([], backend="arbitrary")
    assert collect_visual_elements([], [])["errors"] == []


def test_native_match_is_scoped_to_root_and_preserves_ocr():
    root = {"hwnd": 1, "parent": 0, "pid": 100, "rect": [20, 30, 500, 300]}
    field = {
        "hwnd": 2,
        "parent": 1,
        "pid": 100,
        "rect": [220, 60, 370, 90],
        "name": "UI_GENERAL::STATIC_DATA::Backup Filename",
    }
    foreign_root_field = field | {"hwnd": 3, "parent": 0, "name": "Other"}
    visual = {
        "elements": [
            {
                "root_hwnd": 1,
                "control_type": "input_field_candidate",
                "name": "Backup FiIename",
                "rect": [200, 30, 350, 60],
                "hwnd": None,
            }
        ]
    }
    _associate_visual_nodes(visual, [root, field, foreign_root_field], [root])
    element = visual["elements"][0]
    assert element["name"] == "Backup Filename"
    assert element["ocr_name"] == "Backup FiIename"
    assert element["matching_native_nodes"] == [{"hwnd": 2, "name": field["name"]}]
    assert element["hwnd"] is None

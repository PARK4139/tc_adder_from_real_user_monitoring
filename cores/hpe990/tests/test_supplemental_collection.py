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


def test_collection_keeps_popup_tool_and_modal_images_and_capture_errors(monkeypatch, tmp_path):
    """Regression: Edger lens menus exist as QPopup, not QWidget."""
    from cores.hpe990.functions import step_templates, ui, ui_mapping

    nodes = [
        {"hwnd": index, "parent": 0, "visible": visible, "class_name": cls}
        for index, (cls, visible) in enumerate(
            [
                ("QWidget", True),
                ("QPopup", True),
                ("QTool", True),
                ("#32770", True),
                ("QPopup", False),
            ],
            start=1,
        )
    ]
    attempted = []

    def capture(hwnd, destination):
        attempted.append(hwnd)
        if hwnd == 4:
            raise OSError("Modal capture unavailable")
        return {"hwnd": hwnd, "path": str(destination)}

    monkeypatch.setattr(ui, "session_guard", lambda _: {})
    monkeypatch.setattr(ui, "_native_tree", lambda _: nodes)
    monkeypatch.setattr(ui, "_capture", capture)
    monkeypatch.setattr(ui.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    monkeypatch.setattr(ui, "collect_visual_elements", lambda *a: {"elements": []})
    monkeypatch.setattr(ui, "collect_accessibility", lambda *a, **k: {})
    monkeypatch.setattr(ui, "assign_ui_ids", lambda _: {})
    monkeypatch.setattr(ui_mapping, "target_identity", lambda _: {})
    monkeypatch.setattr(ui_mapping, "inspect_record", lambda *a: {})
    monkeypatch.setattr(ui, "sync_general_expected", lambda: {})
    monkeypatch.setattr(ui, "log_event", lambda *a, **k: None)
    monkeypatch.setattr(step_templates, "template_catalog", lambda _: {})
    result = ui.collect_ui("test", accessibility_backend="none")
    assert attempted == [1, 2, 3, 4]
    assert [capture["hwnd"] for capture in result["screenshots"]] == [1, 2, 3]
    assert result["capture_errors"] == [{"hwnd": 4, "error": "Modal capture unavailable"}]
    assert len(result["nodes"]) == 5

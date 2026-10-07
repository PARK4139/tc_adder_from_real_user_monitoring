"""Evidence boundary and stored-content escaping for the local HTML viewer."""

import json

import pytest

from cores.hpe990.functions import ui_viewer


def test_stored_names_cannot_close_script_element():
    malicious = "</script><script>alert('x')</script>"
    html = ui_viewer.render_html({"name": malicious}, "http://127.0.0.1:1234/token/")
    assert malicious not in html
    assert "\\u003c/script\\u003e" in html


def test_historical_discovery_adds_new_screen_and_rejects_foreign_image(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_viewer.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    sid = "a" * 32
    directory = tmp_path / "ui" / sid / "capture"
    directory.mkdir(parents=True)
    node = {
        "hwnd": 1,
        "parent": 0,
        "name": "New Screen",
        "class_name": "QWidget",
        "visible": True,
        "enabled": True,
        "rect": [0, 0, 100, 100],
    }
    record = {
        "session_id": sid,
        "observed_unix_ms": 1,
        "roots": [node],
        "nodes": [node],
        "screenshots": [],
    }
    path = directory / "inventory.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    first = ui_viewer.viewer_data(sid)
    assert first["windows"][0]["root"]["name"] == "New Screen"
    second = directory.with_name("added")
    second.mkdir()
    record["roots"][0]["name"] = "Future Modal"
    (second / "inventory.json").write_text(json.dumps(record), encoding="utf-8")
    assert ui_viewer.viewer_data(sid)["summary"]["windows"] == 2
    outside = tmp_path / "foreign.png"
    outside.write_bytes(b"foreign")
    record["screenshots"] = [{"hwnd": 1, "path": str(outside)}]
    (second / "inventory.json").write_text(json.dumps(record), encoding="utf-8")
    rejected = ui_viewer.viewer_data(sid)
    assert rejected["read_errors"] and rejected["summary"]["windows"] == 1
    with pytest.raises(ValueError):
        ui_viewer.evidence_root("../foreign")


def test_all_collected_controls_preserve_hidden_and_removed_elements(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_viewer.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    sid = "b" * 32
    root = {
        "hwnd": 1,
        "parent": 0,
        "name": "Screen",
        "class_name": "QWidget",
        "visible": True,
        "enabled": True,
        "rect": [0, 0, 100, 100],
    }
    button = {
        **root,
        "hwnd": 2,
        "parent": 1,
        "name": "pushButton_hidden",
        "visible": False,
        "enabled": False,
    }
    edit = {**root, "hwnd": 3, "parent": 1, "name": "lineEdit_new"}
    for index, nodes in enumerate(([root, button], [root, edit])):
        directory = tmp_path / "ui" / sid / str(index)
        directory.mkdir(parents=True)
        (directory / "inventory.json").write_text(
            json.dumps(
                {
                    "session_id": sid,
                    "observed_unix_ms": index,
                    "roots": [root],
                    "nodes": nodes,
                    "screenshots": [],
                }
            ),
            encoding="utf-8",
        )
    data = ui_viewer.viewer_data(sid)
    assert len(data["all_controls"]) == 3
    assert {n["name"] for n in data["all_controls"]} == {
        "Screen",
        "pushButton_hidden",
        "lineEdit_new",
    }
    hidden = next(n for n in data["all_controls"] if n["hwnd"] == 2)
    assert not hidden["visible"] and not hidden["enabled"]
    assert hidden["path"] == ["Screen", "pushButton_hidden"]


def test_identical_images_group_only_within_session_and_keep_history(tmp_path, monkeypatch):
    from PIL import Image

    monkeypatch.setattr(ui_viewer.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    node = {
        "hwnd": 1,
        "parent": 0,
        "name": "Setup",
        "class_name": "QWidget",
        "visible": True,
        "enabled": True,
        "rect": [0, 0, 10, 10],
    }
    for sid, index, color in [
        ("a" * 32, 1, "white"),
        ("a" * 32, 2, "white"),
        ("a" * 32, 3, "black"),
        ("b" * 32, 1, "white"),
    ]:
        directory = tmp_path / "ui" / sid / str(index)
        directory.mkdir(parents=True)
        image = directory / "screen.png"
        Image.new("RGB", (10, 10), color).save(image)
        (directory / "inventory.json").write_text(
            json.dumps(
                {
                    "session_id": sid,
                    "observed_unix_ms": index,
                    "roots": [node],
                    "nodes": [node],
                    "screenshots": [{"hwnd": 1, "path": str(image)}],
                }
            ),
            encoding="utf-8",
        )
    data = ui_viewer.viewer_data()
    assert data["summary"]["windows"] == 3
    assert data["summary"]["duplicate_screens"] == 1
    grouped = next(w for w in data["windows"] if w["collection_count"] == 2)
    assert grouped["session_id"] == "a" * 32
    assert grouped["observed_unix_ms"] == 2
    assert {o["observed_unix_ms"] for o in grouped["occurrences"]} == {1, 2}


def test_bdd_catalog_changes_revision_and_reports_invalid_registration(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_viewer.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    directory = tmp_path / "ui" / ("a" * 32) / "capture"
    directory.mkdir(parents=True)
    (directory / "inventory.json").write_text(
        json.dumps(
            {
                "session_id": "a" * 32,
                "observed_unix_ms": 1,
                "roots": [],
                "nodes": [],
                "screenshots": [],
            }
        ),
        encoding="utf-8",
    )
    first = ui_viewer.bdd_viewer_data()
    assert first["bdd"]["expected_tests"] == 6 and first["bdd_error"] is None
    updated = {**first["bdd"], "scenarios": first["bdd"]["scenarios"] + [{"name": "Added"}]}
    monkeypatch.setattr(ui_viewer, "bdd_registry", lambda family: updated)
    assert ui_viewer.bdd_viewer_data()["revision"] != first["revision"]

    def invalid(family):
        raise RuntimeError("Unregistered feature")

    monkeypatch.setattr(ui_viewer, "bdd_registry", invalid)
    invalid_data = ui_viewer.bdd_viewer_data()
    assert invalid_data["bdd_error"] == "Unregistered feature"
    assert invalid_data["bdd"]["scenarios"] == []


def test_bdd_screen_has_no_gallery_and_requires_no_collected_ui(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_viewer.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    data = ui_viewer.bdd_viewer_data()
    assert data["summary"]["scenarios"] == 6
    assert not (tmp_path / "ui").exists()
    assert "windows" not in data and "all_controls" not in data
    html = ui_viewer.render_html(data, "http://127.0.0.1:1234/token/")
    assert "BDD 시나리오 목록" in html
    assert "전체 갤러리" not in html and "전체 수집 요소" not in html
    assert "<img" not in html and 'id="screens"' not in html

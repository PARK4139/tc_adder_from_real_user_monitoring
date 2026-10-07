"""Cross-version confirmation, recreation, collision and definition-change guards."""

import json
import sqlite3
from copy import deepcopy

import pytest

from cores.hpe990.functions.ui_mapping import (
    definitions,
    inspect_record,
    resolve_record,
    verify_record,
)

SEMANTIC = "HPE990.Setup.Preferences.General.Language"
DEFINITIONS = {
    SEMANTIC: {
        "semantic_id": SEMANTIC,
        "internal_name": "LanguageInput",
        "root_names": ["Preferences", "환경 설정"],
        "ancestor_names": ["tab_general"],
        "class_name": "QWidget",
        "kind": "combo",
    }
}


def target(version):
    return {"target_id": "HPE990:" + version, "sha256": version, "model": "HPE990"}


def record(handle=1, session="first", root_name="Preferences", field_name="LanguageInput"):
    common = {
        "pid": 42,
        "visible": True,
        "enabled": True,
        "class_name": "QWidget",
        "rect": [0, 0, 100, 100],
    }
    root = common | {"hwnd": handle, "parent": 0, "name": root_name, "ui_id": "UI-000001"}
    tab = common | {
        "hwnd": handle + 1,
        "parent": handle,
        "name": "tab_general",
        "ui_id": "UI-000002",
    }
    field = common | {
        "hwnd": handle + 2,
        "parent": handle + 1,
        "name": field_name,
        "ui_id": "UI-000003",
    }
    return {
        "session_id": session,
        "evidence": session + ".json",
        "observed_unix_ms": 100,
        "nodes": [root, tab, field],
        "roots": [root],
    }


def test_version_confirmation_cannot_cross_builds(tmp_path):
    db = tmp_path / "ids.sqlite3"
    first = record()
    verify_record(first, target("a"), SEMANTIC, "UI-000003", db, DEFINITIONS)
    assert resolve_record(first, target("a"), SEMANTIC, db, DEFINITIONS)["hwnd"] == 3
    with pytest.raises(ValueError, match="No confirmed"):
        resolve_record(first, target("b"), SEMANTIC, db, DEFINITIONS)
    verify_record(first, target("b"), SEMANTIC, "UI-000003", db, DEFINITIONS)
    assert resolve_record(first, target("b"), SEMANTIC, db, DEFINITIONS)["hwnd"] == 3


def test_changed_executable_has_distinct_target_even_without_pe_version(tmp_path):
    from cores.hpe990.functions.ui_mapping import target_identity

    path = tmp_path / "emulator.exe"
    path.write_bytes(b"first fixture binary")
    session = {"processes": [{"exe": str(path)}]}
    first = target_identity(session)
    path.write_bytes(b"second fixture binary")
    second = target_identity(session)
    assert first["target_id"] != second["target_id"]
    assert first["FileVersion"] is None and second["ProductVersion"] is None


def test_dispatch_rechecks_ancestry_after_pre_action_collection(monkeypatch):
    from cores.hpe990.functions import ui

    before = record()
    for node in before["nodes"]:
        node["identity_scope"] = "session_observation"
    changed = deepcopy(before)
    changed["nodes"][1]["name"] = "other_tab"
    trees = iter([before["nodes"], changed["nodes"]])
    monkeypatch.setattr(ui, "session_guard", lambda _: {})
    monkeypatch.setattr(ui, "_native_tree", lambda _: next(trees))
    monkeypatch.setattr(ui, "start_ram", lambda _: {"directory": "fixture"})
    monkeypatch.setattr(ui, "collect_ui", lambda _: before)
    posted = []
    monkeypatch.setattr(ui.win32gui, "PostMessage", lambda *args: posted.append(args))
    with pytest.raises(ValueError, match="ancestry changed"):
        ui.control_ui(
            "first",
            "LanguageInput",
            root_hwnd=1,
            hwnd=3,
            expected_native_path=[
                ["QWidget", "Preferences"],
                ["QWidget", "tab_general"],
                ["QWidget", "LanguageInput"],
            ],
        )
    assert posted == []


def test_recreation_and_reviewed_language_alias_keep_meaning(tmp_path):
    db = tmp_path / "ids.sqlite3"
    verify_record(record(), target("a"), SEMANTIC, "UI-000003", db, DEFINITIONS)
    recreated = record(100, "new", "환경 설정")
    recreated["nodes"][2]["ui_id"] = "UI-008888"
    resolved = resolve_record(recreated, target("a"), SEMANTIC, db, DEFINITIONS)
    assert resolved["semantic_id"] == SEMANTIC
    assert resolved["hwnd"] == 102 and resolved["ui_id"] == "UI-008888"


@pytest.mark.parametrize("change", ["duplicate", "hidden", "disabled", "parent", "name", "clipped"])
def test_changed_or_unusable_candidates_never_resolve(tmp_path, change):
    db = tmp_path / "ids.sqlite3"
    original = record()
    verify_record(original, target("a"), SEMANTIC, "UI-000003", db, DEFINITIONS)
    altered = record(session="changed")
    if change == "duplicate":
        altered["nodes"].append(altered["nodes"][2] | {"hwnd": 44, "ui_id": "UI-000004"})
    elif change == "hidden":
        altered["nodes"][1]["visible"] = False
    elif change == "disabled":
        altered["nodes"][0]["enabled"] = False
    elif change == "parent":
        altered["nodes"][1]["name"] = "other_tab"
    elif change == "name":
        altered["nodes"][2]["name"] = "OtherInput"
    elif change == "clipped":
        altered["nodes"][2]["rect"] = [200, 200, 250, 250]
    with pytest.raises(ValueError):
        resolve_record(altered, target("a"), SEMANTIC, db, DEFINITIONS)
    with pytest.raises(ValueError):
        verify_record(altered, target("a"), SEMANTIC, "UI-000003", db, DEFINITIONS)


def test_definition_change_requires_reconfirmation(tmp_path):
    db = tmp_path / "ids.sqlite3"
    verify_record(record(), target("a"), SEMANTIC, "UI-000003", db, DEFINITIONS)
    changed = deepcopy(DEFINITIONS)
    changed[SEMANTIC]["kind"] = "changed-meaning"
    with pytest.raises(ValueError):
        resolve_record(record(), target("a"), SEMANTIC, db, changed)


def test_all_native_names_paths_and_existing_ids_are_preserved(tmp_path):
    db = tmp_path / "ids.sqlite3"
    report = inspect_record(record(), target("a"), db, DEFINITIONS)
    assert report["observed_native_count"] == 3 and report["unmapped_native_count"] == 2
    with sqlite3.connect(db) as connection:
        rows = connection.execute("SELECT ui_id,data FROM ui_map_observations").fetchall()
    assert len(rows) == 3
    assert json.loads(dict(rows)["UI-000003"])["native_path"][-1] == ["QWidget", "LanguageInput"]


def test_version_variant_supports_renamed_internal_element(tmp_path, monkeypatch):
    from cores.hpe990.common.paths import hpe990_folders

    config = tmp_path / "definitions.json"
    base = deepcopy(DEFINITIONS[SEMANTIC])
    base["variants"] = {"HPE990:b": {"internal_name": "NewLanguageInput"}}
    config.write_text(json.dumps({"definitions": [base]}), encoding="utf-8")
    monkeypatch.setattr(hpe990_folders, "F_HPE990_UI_SEMANTICS", config)
    db = tmp_path / "ids.sqlite3"
    verify_record(record(), target("a"), SEMANTIC, "UI-000003", db, definitions(target("a")))
    second = record(field_name="NewLanguageInput")
    verify_record(second, target("b"), SEMANTIC, "UI-000003", db, definitions(target("b")))
    assert (
        resolve_record(record(), target("a"), SEMANTIC, db, definitions(target("a")))[
            "internal_name"
        ]
        == "LanguageInput"
    )
    assert (
        resolve_record(second, target("b"), SEMANTIC, db, definitions(target("b")))["internal_name"]
        == "NewLanguageInput"
    )

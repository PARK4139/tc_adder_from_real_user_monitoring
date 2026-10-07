"""Identity continuity, conservative linkage, historical evidence and concurrency."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from cores.hpe990.functions.ui_identity import assign_ui_ids


def snapshot(session="a", evidence="one", handle=1):
    root = dict(hwnd=handle, parent=0, pid=100, name="Preferences", class_name="QWidget")
    field = dict(
        hwnd=handle + 1,
        parent=handle,
        pid=100,
        name="UI_GENERAL::STATIC_DATA::Backup Date",
        class_name="QWidget",
    )
    return dict(
        session_id=session,
        evidence=evidence,
        nodes=[root, field],
        roots=[root],
        accessibility={"elements": []},
        visual={"elements": []},
    )


def test_named_identity_survives_handles_sessions_and_geometry(tmp_path):
    database = tmp_path / "ids.sqlite3"
    first, second = snapshot(), snapshot("b", "two", 1000)
    first["nodes"][1]["rect"] = [0, 0, 10, 10]
    second["nodes"][1]["rect"] = [30, 50, 40, 60]
    assign_ui_ids(first, database)
    assign_ui_ids(second, database)
    assert first["nodes"][1]["ui_id"] == second["nodes"][1]["ui_id"]
    assert second["nodes"][1]["identity_scope"] == "semantic_path"
    assert first["roots"][0]["ui_id"] == first["nodes"][0]["ui_id"]


def test_ambiguous_and_unnamed_elements_are_separate_and_scoped(tmp_path):
    first = snapshot()
    first["nodes"] += [first["nodes"][1] | {"hwnd": 3}, first["nodes"][1] | {"hwnd": 4, "name": ""}]
    assign_ui_ids(first, tmp_path / "ids.sqlite3")
    assert len({n["ui_id"] for n in first["nodes"]}) == 4
    assert all(n["identity_scope"] == "session_observation" for n in first["nodes"][1:])
    repeat = deepcopy(first)
    repeat["evidence"] = "repeat"
    assign_ui_ids(repeat, tmp_path / "ids.sqlite3")
    assert [n["ui_id"] for n in first["nodes"]] == [n["ui_id"] for n in repeat["nodes"]]


def test_all_providers_get_ids_and_unique_native_match_shares_id(tmp_path):
    record = snapshot()
    record["visual"]["elements"] = [
        dict(
            id="v:1",
            pid=100,
            root_hwnd=1,
            hwnd=None,
            name="Backup Date",
            matching_native_nodes=[{"hwnd": 2}],
        ),
        dict(id="v:2", pid=100, root_hwnd=1, hwnd=None, name="unknown"),
    ]
    record["accessibility"]["elements"] = [
        dict(id="a:1", pid=100, root_hwnd=1, hwnd=2, name="Backup Date"),
        dict(id="a:2", pid=200, root_hwnd=1, hwnd=2, name="foreign"),
    ]
    registry = assign_ui_ids(record, tmp_path / "ids.sqlite3")
    field_id = record["nodes"][1]["ui_id"]
    assert record["visual"]["elements"][0]["ui_id"] == field_id
    assert record["accessibility"]["elements"][0]["ui_id"] == field_id
    assert record["accessibility"]["elements"][1]["ui_id"] != field_id
    assert record["visual"]["elements"][1]["ui_id"] != field_id
    assert registry["unique_elements"] == 4


def test_historical_assignment_does_not_change_on_reindex(tmp_path):
    database = tmp_path / "ids.sqlite3"
    record = snapshot()
    assign_ui_ids(record, database)
    old_id = record["nodes"][1]["ui_id"]
    # Later processing cannot silently change an already indexed evidence alias.
    record["nodes"][1]["name"] = "changed interpretation"
    assign_ui_ids(record, database)
    assert record["nodes"][1]["ui_id"] == old_id
    new = snapshot("new", "new")
    new["nodes"][1]["name"] = "New field"
    assign_ui_ids(new, database)
    assert int(new["nodes"][1]["ui_id"][3:]) > int(old_id[3:])


def test_concurrent_mcp_writers_share_one_identity(tmp_path):
    database = tmp_path / "ids.sqlite3"

    def collect(index):
        record = snapshot(str(index), str(index), index * 10 + 1)
        assign_ui_ids(record, database)
        return [n["ui_id"] for n in record["nodes"]]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect, range(12)))
    assert all(ids == results[0] for ids in results)


def test_catalog_indexes_legacy_evidence_without_rewriting(monkeypatch, tmp_path):
    import json

    from cores.hpe990.functions import ui

    monkeypatch.setattr(ui, "session_guard", lambda *args: None)
    monkeypatch.setattr(ui.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    monkeypatch.setattr(ui.hpe990_folders, "F_HPE990_UI_REGISTRY", tmp_path / "ids.sqlite3")
    originals = {}
    for index in range(2):
        path = tmp_path / "ui" / "test-session" / str(index) / "inventory.json"
        path.parent.mkdir(parents=True)
        record = snapshot("test-session", str(path), index * 10 + 1)
        record.update(observed_unix_ms=index, screenshots=[])
        path.write_text(json.dumps(record), encoding="utf-8")
        originals[path] = path.read_bytes()
    result = ui.ui_catalog("test-session")
    assert result["unique_native_controls"] == 2
    assert result["ui_registry"]["unique_elements"] == 2
    assert all(len(c["observations"]) == 2 for c in result["controls"])
    assert all(path.read_bytes() == content for path, content in originals.items())


def test_catalog_reuses_registered_snapshot_without_reallocating_ids(monkeypatch, tmp_path):
    import json

    from cores.hpe990.functions import ui

    monkeypatch.setattr(ui, "session_guard", lambda *args: None)
    monkeypatch.setattr(ui.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    monkeypatch.setattr(ui.hpe990_folders, "F_HPE990_UI_REGISTRY", tmp_path / "ids.sqlite3")
    path = tmp_path / "ui" / "test-session" / "registered" / "inventory.json"
    path.parent.mkdir(parents=True)
    record = snapshot("test-session", str(path), 1)
    record.update(observed_unix_ms=1, screenshots=[])
    record["ui_registry"] = assign_ui_ids(record, tmp_path / "ids.sqlite3")
    path.write_text(json.dumps(record), encoding="utf-8")
    original = path.read_bytes()

    def unexpected_registration(_):
        raise AssertionError("Historical registered snapshots must not repeat SSOT writes")

    monkeypatch.setattr(ui, "assign_ui_ids", unexpected_registration)
    result = ui.ui_catalog("test-session")
    assert result["unique_native_controls"] == 2
    assert result["ui_registry"]["elements"] == record["ui_registry"]["elements"]
    assert path.read_bytes() == original
    assert result["registry_reuse"] == {"reused_snapshots": 1, "indexed_snapshots": 0}


def test_catalog_rechecks_snapshot_definitions_against_current_ssot(monkeypatch, tmp_path):
    import json

    from cores.hpe990.functions import ui

    monkeypatch.setattr(ui, "session_guard", lambda *args: None)
    monkeypatch.setattr(ui.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    monkeypatch.setattr(ui.hpe990_folders, "F_HPE990_UI_REGISTRY", tmp_path / "ids.sqlite3")
    path = tmp_path / "ui" / "test-session" / "changed" / "inventory.json"
    path.parent.mkdir(parents=True)
    record = snapshot("test-session", str(path), 1)
    record.update(observed_unix_ms=1, screenshots=[])
    correct = assign_ui_ids(record, tmp_path / "ids.sqlite3")
    record["ui_registry"] = json.loads(json.dumps(correct))
    record["ui_registry"]["elements"][0]["selector"] = ["incorrect"]
    path.write_text(json.dumps(record), encoding="utf-8")
    original = path.read_bytes()
    result = ui.ui_catalog("test-session")
    assert result["ui_registry"]["elements"] == correct["elements"]
    assert result["registry_reuse"] == {"reused_snapshots": 0, "indexed_snapshots": 1}
    assert path.read_bytes() == original

"""Dynamic expectations use observed UI definitions and preserve authored cases."""

import json
import sqlite3

from cores.hpe990.functions.tc_dynamic import general_elements, sync_general_expected


def insert(db, name):
    db.execute(
        "INSERT INTO elements(selector) VALUES (?)",
        (json.dumps(["native", json.dumps([["QWidget", name]])]),),
    )


def test_new_collected_element_updates_expected_without_authored_list(tmp_path):
    database = tmp_path / "ui.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE elements(number INTEGER PRIMARY KEY,selector TEXT)")
        insert(db, "UI_GENERAL::WIDGET::Language")
        insert(db, "UI_GENERAL::COMBO::Language")
        insert(db, "UI_GENERAL::GROUP::Sleep Mode")
        insert(db, "UI_OTHER::INPUT::Foreign field")
    source = tmp_path / "test.feature"
    source.write_text(
        """@path-Setup/Preferences/General
Feature: Dynamic
  @TC-010 @expected-collected-General
  Scenario: TC-010 General
    Given Ready
    When Scroll
    # BEGIN collected General elements
    Then Old expected
    # END collected General elements
  @TC-030
  Scenario: TC-030 Unchanged
    When Select
    Then Authored result
""",
        encoding="utf-8",
    )
    markdown = source.with_suffix(".md")
    markdown.write_text(
        "### TC-010 General\n| 2 | scroll | old |\n### TC-030 Unchanged\nKeep me\n",
        encoding="utf-8",
    )
    result = sync_general_expected(database, source)
    assert result["element_count"] == 2
    assert result["executed"] is False
    content = source.read_text(encoding="utf-8")
    assert "Then 하기 수집 요소가 각각 보여야 합니다." in content
    assert content.count("    And Language\n") == 1
    assert "    And Sleep Mode\n" in content
    assert "항목이 표시된다" not in content
    assert "Foreign field" not in content
    with sqlite3.connect(database) as db:
        insert(db, "UI_GENERAL::STATIC_DATA::Backup Date")
    assert sync_general_expected(database, source)["element_count"] == 3
    assert "    And Backup Date\n" in source.read_text(encoding="utf-8")
    assert "<br>Backup Date<br>" in markdown.read_text(encoding="utf-8")
    assert "Then Authored result" in source.read_text(encoding="utf-8")
    assert markdown.read_text(encoding="utf-8").endswith("### TC-030 Unchanged\nKeep me\n")
    assert sync_general_expected(database, source)["updated"] is False


def test_missing_collection_does_not_invent_elements(tmp_path):
    database = tmp_path / "missing.sqlite3"
    assert general_elements(database) == []
    assert sync_general_expected(database, tmp_path / "missing.feature")["updated"] is False


def test_default_sync_updates_only_individual_tc_file(tmp_path, monkeypatch):
    from cores.hpe990.common.paths import hpe990_folders

    cases = tmp_path / "cases"
    (cases / "to_review").mkdir(parents=True)
    monkeypatch.setattr(hpe990_folders, "D_HPE990_TC_CASES", cases)
    source = cases / "to_review" / "TC-010.feature"
    source.write_text(
        "@path-Setup/Preferences/General\nFeature: General\n"
        "  @TC-010 @expected-collected-General\n  Scenario: TC-010 General\n"
        "    When Scroll\n    # BEGIN collected General elements\n"
        "    Then Old\n    # END collected General elements\n",
        encoding="utf-8",
    )
    other = cases / "to_review" / "TC-030.feature"
    other.write_text("Untouched authoring file", encoding="utf-8")
    database = tmp_path / "ui.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE elements(number INTEGER PRIMARY KEY,selector TEXT)")
        insert(db, "UI_GENERAL::WIDGET::Language")
    result = sync_general_expected(database)
    assert result["updated"] is True
    assert result["source"] == str(source)
    assert "And Language" in source.read_text(encoding="utf-8")
    assert other.read_text(encoding="utf-8") == "Untouched authoring file"


def test_reviewed_case_and_markdown_unchanged_until_moved_back(tmp_path, monkeypatch):
    from cores.hpe990.common.paths import hpe990_folders

    cases = tmp_path / "tc"
    reviewed = cases / "reviewed" / "setup" / "TC-010.feature"
    reviewed.parent.mkdir(parents=True)
    monkeypatch.setattr(hpe990_folders, "D_HPE990_TC_CASES", cases)
    authored = (
        "@path-Setup/Preferences/General\nFeature: General\n"
        "  @TC-010 @expected-collected-General\n  Scenario: TC-010 General\n"
        "    When Scroll\n    # BEGIN collected General elements\n"
        "    Then Reviewed content\n    # END collected General elements\n"
    ).encode()
    reviewed.write_bytes(authored)
    markdown = reviewed.with_suffix(".md")
    markdown.write_text("Reviewed companion", encoding="utf-8")
    database = tmp_path / "ui.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE elements(number INTEGER PRIMARY KEY,selector TEXT)")
        insert(db, "UI_GENERAL::STATIC_DATA::Newly observed field")
    original_mtime = reviewed.stat().st_mtime_ns
    for explicit_source in (None, reviewed, reviewed.parent / ".." / "setup" / reviewed.name):
        result = sync_general_expected(database, explicit_source)
        assert result["updated"] is False
        assert result["review_state"] == "reviewed"
        assert "protected" in result["reason"]
    assert reviewed.read_bytes() == authored
    assert reviewed.stat().st_mtime_ns == original_mtime
    assert markdown.read_text(encoding="utf-8") == "Reviewed companion"
    assert not reviewed.with_suffix(".feature.lock").exists()
    pending = cases / "to_review" / "setup" / reviewed.name
    pending.parent.mkdir(parents=True)
    reviewed.rename(pending)
    assert sync_general_expected(database)["updated"] is True
    assert "And Newly observed field" in pending.read_text(encoding="utf-8")
    assert markdown.read_text(encoding="utf-8") == "Reviewed companion"

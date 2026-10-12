"""Verify independent authoring files, live inventory and cross-file validation."""

import json

import pytest
from gherkin.parser import Parser

from cores.hpe990.functions.tc_repository import load_review_source, review_stamp
from cores.hpe990.scripts.render_tc_review import render_review
from cores.hpe990.tests.test_tc_review import draft


def repository(tmp_path, order):
    directory = tmp_path / "cases"
    (directory / "to_review").mkdir(parents=True)
    (directory / "reviewed").mkdir()
    config = tmp_path / "order.json"
    config.write_text(json.dumps({"order": order}), encoding="utf-8")
    return directory, config


def test_edit_add_delete_and_explicit_order(tmp_path):
    directory, config = repository(tmp_path, ["TC-020", "TC-010"])
    first = directory / "to_review" / "TC-010.feature"
    first.write_text(draft("TC-010"), encoding="utf-8")
    before = review_stamp(directory, config)
    first.write_text(draft("TC-010").replace("Field", "언어 설정 및 적용 확인"), encoding="utf-8")
    assert review_stamp(directory, config) != before
    second = directory / "to_review" / "TC-020.feature"
    second.write_text(draft("TC-020", feature_path="Setup/Other"), encoding="utf-8")
    source = load_review_source(directory, config)
    assert source.index("Scenario: TC-020") < source.index("Scenario: TC-010")
    html, summary = render_review(source)
    assert summary["tc_count"] == 2
    assert "언어 설정 및 적용 확인" in html
    assert "Setup &gt; Other" in html
    stamp = review_stamp(directory, config)
    second.unlink()
    assert review_stamp(directory, config) != stamp
    assert render_review(load_review_source(directory, config))[1]["tc_count"] == 1


def test_new_file_is_discovered_without_order_entry(tmp_path):
    directory, config = repository(tmp_path, ["TC-020"])
    for identity in ("TC-010", "TC-020", "TC-030"):
        (directory / "to_review" / f"{identity}.feature").write_text(
            draft(identity), encoding="utf-8"
        )
    children = Parser().parse(load_review_source(directory, config))["feature"]["children"]
    assert [c["scenario"]["name"].split()[0] for c in children] == ["TC-020", "TC-010", "TC-030"]


def test_duplicate_file_identity_is_rejected(tmp_path):
    directory, config = repository(tmp_path, ["TC-020"])
    (directory / "to_review" / "TC-020.feature").write_text(draft(), encoding="utf-8")
    other = directory / "reviewed" / "other"
    other.mkdir()
    (other / "TC-020.feature").write_text(draft(), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_review_source(directory, config)


def test_filename_mismatch_and_multiple_scenarios_rejected(tmp_path):
    directory, config = repository(tmp_path, ["TC-020"])
    path = directory / "to_review" / "TC-010.feature"
    path.write_text(draft(), encoding="utf-8")
    with pytest.raises(ValueError, match="filename mismatch"):
        load_review_source(directory, config)
    path.write_text(
        draft("TC-010") + "\n  Scenario: Another\n    When Click\n    Then Done\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="one Scenario"):
        load_review_source(directory, config)


def test_folder_move_changes_only_review_state(tmp_path, monkeypatch):
    from cores.hpe990.common.paths import hpe990_folders
    from cores.hpe990.functions.tc_repository import case_file

    directory, config = repository(tmp_path, ["TC-020"])
    monkeypatch.setattr(hpe990_folders, "D_HPE990_TC_CASES", directory)
    source = directory / "to_review" / "TC-020.feature"
    source.write_text(draft(), encoding="utf-8")
    content = source.read_bytes()
    before = load_review_source(directory, config)
    stamp = review_stamp(directory, config)
    html, _ = render_review(before)
    assert "검수 대기" in html
    destination = directory / "reviewed" / source.name
    source.rename(destination)
    assert case_file("TC-020") == destination
    assert review_stamp(directory, config) != stamp
    after = load_review_source(directory, config)
    assert before.replace("@review-to_review", "@review-reviewed") == after
    assert destination.read_bytes() == content
    assert "검수 완료" in render_review(after)[0]
    destination.rename(source)
    assert load_review_source(directory, config) == before


def test_authored_review_tag_and_orphan_file_rejected(tmp_path):
    directory, config = repository(tmp_path, ["TC-020"])
    source = directory / "to_review" / "TC-020.feature"
    source.write_text("@review-reviewed\n" + draft(), encoding="utf-8")
    with pytest.raises(ValueError, match="folder, not authored tags"):
        load_review_source(directory, config)
    source.write_text(draft(), encoding="utf-8")
    source.rename(directory / source.name)
    with pytest.raises(ValueError, match="under to_review or reviewed"):
        load_review_source(directory, config)

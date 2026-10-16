"""Validate TC identity and tree-path separation without running the Emulator."""

import json

import pytest

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.tc_repository import load_review_source
from cores.hpe990.scripts.render_tc_review import TEST_TARGET, render_review


def draft(identity="TC-020", scenario_path="", feature_path="Setup/Preferences/General"):
    return f"""@path-{feature_path}
Feature: Review
  @{identity} @type-number {scenario_path}
  Scenario: {identity} Field
    Given Ready
    When Select
    Then Visible
"""


def test_tc_identity_survives_tree_move():
    original, _ = render_review(draft())
    moved, _ = render_review(draft(scenario_path="@path-Setup/Export%20Options"))
    for document in (original, moved):
        assert 'id="TC-020"' in document
        assert 'href="#TC-020"' in document
    target_path = f"/{TEST_TARGET['model']}/{TEST_TARGET['version']}"
    assert f'data-node="{target_path}/Setup/Preferences/General"' in original
    assert f'data-node="{target_path}/Setup/Export Options"' in moved
    assert f"{TEST_TARGET['model']} &gt; {TEST_TARGET['version']} &gt; Setup &gt; Export Options" in moved


@pytest.mark.parametrize("identity", ["TC-Setup-General-022", "TC-22", "TC-000", "TC-0022"])
def test_noncanonical_id_is_rejected(identity):
    with pytest.raises(ValueError):
        render_review(draft(identity))


def test_duplicate_id_across_paths_is_rejected():
    source = (
        draft()
        + """
  @TC-020 @path-Setup/Other
  Scenario: Another
    When Select
    Then Visible
"""
    )
    with pytest.raises(ValueError, match="Duplicate"):
        render_review(source)


def test_actual_drafts_match_issued_ids():
    root = hpe990_folders.D_HPE990
    source = load_review_source()
    ledger = json.loads((root / "configs/tc_ids.json").read_text(encoding="utf-8"))
    document, summary = render_review(source)
    ids = ledger["issued_ids"]
    assert len(ids) == len(set(ids)) == summary["tc_count"]
    assert summary["step_groups"] >= summary["tc_count"]
    assert ledger["next_number"] == max(int(identity[3:]) for identity in ids) + 10
    assert ids == [f"TC-{n:03d}" for n in range(10, ledger["next_number"], 10)]
    assert not set(ledger["retired_ids"]) & set(ids)
    assert len(ledger["renumber_migrations"][-1]["mapping"]) == 24
    for identity in ids:
        assert document.count(f'id="{identity}"') == 1
        assert document.count(f'href="#{identity}"') == 1
    assert "TC-Setup-" not in document


def test_actual_review_uses_screen_and_function_suites_without_duplicate_cases():
    document, _ = render_review(load_review_source())
    target = f"/{TEST_TARGET['model']}/{TEST_TARGET['version']}"
    for path in (
        "/Edger/Setup/Preferences/General",
        "/Edger",
        "/Edger/Job Manager",
        "/Edger/Job Editor",
        "/Edger/Digital Pattern",
        "/Edger/Hole Editor",
    ):
        assert f'data-node="{target}{path}"' in document
    assert f'data-node="{target}/Setup"' not in document
    assert f'data-node="{target}/Edger/Setup/Preferences/General/' not in document
    assert f'data-node="{target}/Edger/작업 불러오기' not in document
    assert document.index('href="#TC-1740"') < document.index(
        f'data-node="{target}/Edger/Job Manager"'
    )
    assert document.index(f'data-node="{target}/Edger/Hole Editor"') < document.index(
        f'data-node="{target}/Edger/Setup"'
    )
    assert "Sleep Mode &gt;" not in document.split('<div id="results">')[0]
    for number in (250, 260, 270, 280, 1690, 1700, 1710, 1720, 1730, 1740):
        assert document.count(f'id="TC-{number}"') == 1
        assert document.count(f'href="#TC-{number}"') == 1


def test_four_digit_id_and_explicit_path_required():
    document, _ = render_review(draft("TC-1000"))
    assert 'id="TC-1000"' in document
    with pytest.raises(ValueError, match="@path-"):
        render_review(draft().replace("@path-Setup/Preferences/General", ""))


def test_tc_1720_uses_action_steps_and_compares_loaded_job_info():
    document, _ = render_review(load_review_source())
    start = document.index('<article class="tc" id="TC-1720">')
    card = document[start : document.index("</article>", start)]
    assert "Edger 화면에서 폴더 버튼 클릭" in card
    assert "Job Manager에서 설치 샘플 탭 선택" in card
    assert "CIRCLE 작업 선택" in card
    assert "Digital Pattern·Hole Editor 화면 이동 후 작업 정보 유지 확인" in card
    assert "작업 번호와 도형이 사전조건에서 확인한 값과 같아야 합니다." in card
    assert "한다" not in card
    assert "시험 시작 시 작업 번호·도형·속성을 비교 기준으로 기록" not in card


def test_dictionary_violation_is_rejected_before_review_export():
    with pytest.raises(ValueError, match="TC up dictionary violation"):
        render_review(draft().replace("Then Visible", "Then 설정값이 표시된다"))
    render_review(draft().replace("Then Visible", "Then 설정값이 보여야 합니다."))

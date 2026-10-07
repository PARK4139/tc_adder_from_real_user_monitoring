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
    assert "Setup &gt; Export Options" in moved


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
    assert len(ids) == len(set(ids)) == summary["tc_count"] == 24
    assert summary["step_groups"] >= summary["tc_count"]
    assert ledger["next_number"] == 250
    assert ids == [f"TC-{n:03d}" for n in range(10, 250, 10)]
    assert not set(ledger["retired_ids"]) & set(ids)
    assert len(ledger["renumber_migrations"][-1]["mapping"]) == 24
    for identity in ids:
        assert document.count(f'id="{identity}"') == 1
        assert document.count(f'href="#{identity}"') == 1
    assert "TC-Setup-" not in document


def test_four_digit_id_and_explicit_path_required():
    document, _ = render_review(draft("TC-1000"))
    assert 'id="TC-1000"' in document
    with pytest.raises(ValueError, match="@path-"):
        render_review(draft().replace("@path-Setup/Preferences/General", ""))


def test_dictionary_violation_is_rejected_before_review_export():
    with pytest.raises(ValueError, match="TC up dictionary violation"):
        render_review(draft().replace("Then Visible", "Then 설정값이 표시된다"))
    render_review(draft().replace("Then Visible", "Then 설정값이 보여야 합니다."))

"""Template drafts preserve uncertainty and bind every observed UI ID."""

import json

import pytest

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.step_templates import _review_html, generate_drafts


def definitions():
    return json.loads(hpe990_folders.F_HPE990_STEP_TEMPLATES.read_text(encoding="utf-8"))[
        "templates"
    ]


def test_static_field_does_not_get_edit_steps_and_unknown_is_not_dropped():
    elements = [
        dict(ui_id="UI-000111", name="UI_GENERAL::STATIC_DATA::Backup Date"),
        dict(ui_id="UI-000112", name="", hwnd=None),
    ]
    drafts = generate_drafts(elements, definitions(), {})
    assert [d["ui_id"] for d in drafts] == [e["ui_id"] for e in elements]
    assert drafts[0]["ui_type"] == "display"
    assert "입력" not in str(drafts[0]["cases"][0]["steps"])
    assert "expected_display_value" in drafts[0]["cases"][0]["pending_specifications"]
    assert drafts[1]["ui_type"] == "unknown"
    assert "ui_name" in drafts[1]["cases"][0]["pending_specifications"]
    assert all(not case["executable"] for draft in drafts for case in draft["cases"])


def test_selector_exact_numbered_groups_use_supplied_specs_and_no_new_tc_id():
    element = dict(ui_id="UI-000114", name="UI_GENERAL::COMBO::Language")
    binding = {
        "UI-000114": {
            "ui_type": "option-selector",
            "type_verified": True,
            "parameters": {
                "first_value": "English",
                "second_value": "Korean",
                "value_description": "지원 언어",
                "screen_expected_result": "설정 영역이 보여야 합니다.",
                "save_action": "Save 클릭",
                "reopen_action": "Preferences 재진입",
                "tab_select_action": "General 탭 선택",
            },
        }
    }
    draft = generate_drafts([element], definitions(), binding)[0]
    case = draft["cases"][0]
    assert case["steps"][0]["Steps"] == ["Setup > Preferences > General 탭 선택"]
    assert case["steps"][1]["Steps"] == ["Language 선택기의 화살표 조작 후 English 선택"]
    assert case["steps"][1]["Expected Result"] == ["Language에 English가 보여야 합니다."]
    assert [s["Step"] for s in case["steps"]] == [1, 2, 3, 4, 5]
    assert case["pending_specifications"] == []
    assert case["status"] == "draft" and not case["executable"]
    assert "tc_id" not in draft


def test_boundary_cases_keep_min_max_inclusive_and_exclusive_pending():
    element = dict(ui_id="UI-000083", name="UI_GENERAL::INPUT::Wait (minutes)")
    draft = generate_drafts([element], definitions(), {}, [("Wait (minutes) 숫자 입력", "number")])[
        0
    ]
    assert draft["ui_type"] == "number" and not draft["type_verified"]
    boundary = draft["cases"][1]
    assert boundary["template_id"] == "number-boundary"
    assert len(boundary["steps"]) == 5
    assert boundary["source_tc_ids"] == ["TC-015"]
    boundary = next(
        case for case in draft["cases"] if case["template_id"] == "number-boundary-extended"
    )
    assert len(boundary["steps"]) == 6
    assert {
        "minimum",
        "maximum",
        "below_minimum",
        "above_maximum",
        "at_or_above_minimum",
        "at_or_below_maximum",
    } <= set(boundary["pending_specifications"])


@pytest.mark.parametrize(
    "kind",
    [
        "window",
        "modal",
        "popup",
        "checkbox",
        "radio",
        "button",
        "input-field",
        "save-reopen",
        "cancel-reopen",
    ],
)
def test_templates_have_individual_preconditions_and_valid_action_phrases(kind):
    element = dict(ui_id="UI-000001", name="<test>")
    draft = generate_drafts([element], definitions(), {"UI-000001": {"ui_type": kind}})[0]
    case = draft["cases"][0]
    assert case["preconditions"][0]["Step"] == 1
    assert case["pending_specifications"]
    for step in case["steps"]:
        assert step["Steps"] and step["Expected Result"]
        assert all(not text.endswith(("한다", "된다", "한다.", "된다.")) for text in step["Steps"])
    document = _review_html([draft])
    assert "&lt;test&gt;" in document and "<test>" not in document
    assert "<th>Step</th><th>Steps</th><th>Expected Result</th>" in document


def test_unknown_binding_type_and_name_override_are_rejected():
    element = dict(ui_id="UI-000001", name="Observed")
    with pytest.raises(ValueError):
        generate_drafts([element], definitions(), {"UI-000001": {"ui_type": "fiction"}})
    with pytest.raises(ValueError):
        generate_drafts([element], definitions(), {"UI-000001": {"parameters": {"name": "fake"}}})

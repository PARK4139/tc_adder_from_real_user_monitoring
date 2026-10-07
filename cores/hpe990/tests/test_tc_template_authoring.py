"""Current authored TCs supply full workflows, prerequisites and source traceability."""

import json

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.tc_template_authoring import compile_tc_templates


def test_current_tc_patterns_preserve_flow_and_dictionary_wording():
    source = (hpe990_folders.D_HPE990 / "docs/bdd/preferences_general.feature").read_text(
        encoding="utf-8"
    )
    existing = json.loads(hpe990_folders.F_HPE990_STEP_TEMPLATES.read_text(encoding="utf-8"))
    compiled = compile_tc_templates(source, existing)
    assert compiled["authored_template_count"] == 9
    templates = compiled["templates"]
    for kind in ("option-selector", "radio", "checkbox", "number"):
        assert len(templates[kind]["steps"]) == 5
        assert templates[kind]["preconditions"]
        assert templates[kind]["source_tc_ids"]
        assert templates[kind]["type_verified"] is False
    assert templates["radio"]["related_tc_ids"] == [
        f"TC-{n:03d}" for n in (40, 50, 100, 110, 120, 130, 140, 150, 160, 200)
    ]
    assert len(templates["button-save"]["steps"]) == 4
    assert len(templates["button-cancel"]["steps"]) == 4
    assert templates["input-field"]["source_limit"]
    invalid = templates["number-invalid"]
    assert len(invalid["steps"]) == 7
    outcomes = str(invalid["steps"])
    for field in (
        "empty_value_result",
        "non_numeric_value_result",
        "below_minimum_result",
        "above_maximum_result",
    ):
        assert "{" + field + "}" in outcomes
    assert all(
        "표시된다" not in text
        for template in templates.values()
        for step in template["steps"]
        for text in step["Expected Result"]
    )
    assert compile_tc_templates(source, compiled) == compiled

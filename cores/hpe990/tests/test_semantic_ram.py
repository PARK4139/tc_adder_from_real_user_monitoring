"""Validate observed value/text changes and refusal to infer across collection gaps."""

from copy import deepcopy

import pytest

from cores.hpe990.functions.semantic_ram import (
    _native_signature,
    affected_elements,
    semantic_changes,
    semantic_start,
)


def record():
    return {
        "nodes": [
            {
                "hwnd": 1,
                "class_name": "QWidget",
                "ui_id": "UI-000001",
                "name": "old",
                "enabled": True,
                "visible": True,
                "rect": [0, 0, 100, 100],
            }
        ],
        "accessibility": {
            "elements": [{"ui_id": "UI-000002", "root_hwnd": 1, "name": "Wait", "value": "5"}],
            "errors": [],
        },
        "visual": {
            "elements": [
                {
                    "ui_id": "UI-000003",
                    "root_hwnd": 1,
                    "control_type": "input_field_candidate",
                    "rect": [10, 20, 80, 40],
                    "name": "Wait",
                    "observed_text": "5",
                }
            ],
            "errors": [],
        },
    }


def test_readable_value_and_ocr_input_are_distinguished():
    before = record()
    after = deepcopy(before)
    after["accessibility"]["elements"][0]["value"] = "6"
    after["visual"]["elements"][0]["observed_text"] = "6"
    changes = semantic_changes(before, after)
    assert [(c["kind"], c["semantic_state_verified"]) for c in changes] == [
        ("value_changed", True),
        ("ocr_input_changed", False),
    ]
    assert all(c["before"] == "5" and c["after"] == "6" for c in changes)


def test_provider_timeout_does_not_create_value_changes():
    before = record()
    after = deepcopy(before)
    after["accessibility"]["errors"] = ["timeout"]
    after["accessibility"]["elements"][0]["value"] = "9"
    assert semantic_changes(before, after) == []


def test_unreadable_value_is_not_treated_as_empty():
    before = record()
    after = deepcopy(before)
    after["accessibility"]["elements"][0]["value"] = None
    assert semantic_changes(before, after) == []


def test_ocr_text_width_change_still_compares_content():
    before = record()
    before["visual"]["elements"][0].update(control_type="text", name="5")
    after = deepcopy(before)
    after["visual"]["elements"][0].update(name="1000", rect=[10, 20, 110, 40])
    changes = semantic_changes(before, after)
    assert changes[0]["kind"] == "text_changed"
    assert changes[0]["before"] == "5" and changes[0]["after"] == "1000"


def test_ambiguous_ocr_locations_are_not_matched():
    before = record()
    before["visual"]["elements"].append(deepcopy(before["visual"]["elements"][0]))
    after = deepcopy(before)
    after["visual"]["elements"][0]["observed_text"] = "6"
    assert semantic_changes(before, after) == []


def test_new_and_removed_visual_text_are_observations():
    before = record()
    after = deepcopy(before)
    after["visual"]["elements"][0].update(rect=[90, 20, 160, 40], observed_text="9")
    changes = semantic_changes(before, after)
    assert {c["kind"] for c in changes} == {
        "ocr_element_observed",
        "ocr_element_no_longer_observed",
    }
    assert all(not c["semantic_state_verified"] for c in changes)


def test_color_region_links_only_overlapping_descendants():
    root = record()["nodes"][0] | {"parent": 0}
    child = root | {"hwnd": 2, "parent": 1, "rect": [10, 10, 20, 20], "ui_id": "UI-000002"}
    foreign = child | {"hwnd": 3, "parent": 0, "ui_id": "UI-000003"}
    associated = affected_elements(
        {"nodes": [root, child, foreign]}, 1, [{"rect": [12, 12, 13, 13]}]
    )
    assert [e["ui_id"] for e in associated] == ["UI-000002"]
    assert associated[0]["association"] == "geometry_overlap_candidate"


def test_unchanged_sample_signature_ignores_identity_metadata():
    before = record()
    after = deepcopy(before)
    after["nodes"][0]["identity_scope"] = "semantic_path"
    assert _native_signature(before) == _native_signature(after)
    after["nodes"][0]["visible"] = False
    assert _native_signature(before) != _native_signature(after)


@pytest.mark.parametrize("interval", [True, 0, 99, 10001])
def test_invalid_interval_is_rejected_before_start(interval):
    with pytest.raises(ValueError):
        semantic_start("unused", interval_ms=interval)

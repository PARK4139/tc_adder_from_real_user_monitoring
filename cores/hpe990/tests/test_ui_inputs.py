"""Input inventory includes unknown/hidden fields without claiming editing success."""

from cores.hpe990.functions.ui_inputs import build_input_ledger


def test_unknown_hidden_readonly_and_editable_are_retained():
    record = {
        "observed_unix_ms": 10,
        "evidence": "inventory.json",
        "nodes": [
            {
                "ui_id": "UI-000010",
                "name": "UI_GENERAL::INPUT::Config DB History",
                "visible": False,
            },
            {"ui_id": "UI-000020", "name": "lineEdit_value", "visible": True},
        ],
        "accessibility": {
            "elements": [
                {
                    "ui_id": "UI-000030",
                    "control_type": "Edit",
                    "readonly": True,
                    "value": "original",
                },
                {"ui_id": "UI-000040", "role": 42, "readonly": False, "value": "5"},
            ]
        },
        "visual": {
            "elements": [
                {
                    "ui_id": "UI-000050",
                    "control_type": "input_field_candidate",
                    "name": "Backup Date",
                }
            ]
        },
    }
    result = build_input_ledger([record])
    assert result["summary"]["input_count"] == 5
    assert result["summary"]["editability"] == {"unknown": 3, "readonly": 1, "provider_editable": 1}
    assert result["summary"]["replacement_verified_count"] == 0
    assert result["inputs"][0]["latest"]["visible"] is False


def test_same_ui_id_preserves_observation_history():
    first = {
        "observed_unix_ms": 1,
        "evidence": "first.json",
        "nodes": [{"ui_id": "UI-000010", "name": "lineEdit_value", "visible": True}],
    }
    second = {
        "observed_unix_ms": 2,
        "evidence": "second.json",
        "nodes": [{"ui_id": "UI-000010", "name": "lineEdit_value", "visible": False}],
    }
    result = build_input_ledger([second, first])
    assert result["summary"]["input_count"] == 1
    assert len(result["inputs"][0]["observations"]) == 2
    assert result["inputs"][0]["latest"]["evidence"] == "second.json"

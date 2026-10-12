"""Refuse stale, ambiguous or unavailable OCR targets before input."""

from copy import deepcopy

import pytest

from cores.hpe990.functions.ui_visual_control import resolve_visual


def inventory():
    root = {"hwnd": 1, "visible": True, "enabled": True}
    target = {
        "ui_id": "UI-000010",
        "root_hwnd": 1,
        "root_ui_id": "UI-000001",
        "name": "Preferences",
        "control_type": "text",
        "rect_space": "root_screenshot_pixels",
        "screenshot_sha256": "current",
        "rect": [10, 20, 30, 40],
    }
    return {
        "roots": [root],
        "visual": {"elements": [target]},
        "screenshots": [{"hwnd": 1, "sha256": "current"}],
    }


def test_unique_label_rebind_uses_fresh_geometry():
    record = inventory()
    old = deepcopy(record["visual"]["elements"][0])
    old["ui_id"] = "UI-000009"
    old["rect"] = [0, 0, 10, 10]
    result, _, _ = resolve_visual(record, old["ui_id"], old)
    assert result["rect"] == [10, 20, 30, 40]


def test_ambiguous_label_is_rejected():
    record = inventory()
    old = deepcopy(record["visual"]["elements"][0])
    record["visual"]["elements"].append({**old, "ui_id": "UI-000011"})
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_visual(record, "UI-000009", old)


def test_disabled_root_and_stale_image_rejected():
    record = inventory()
    record["roots"][0]["enabled"] = False
    with pytest.raises(ValueError, match="hidden/disabled"):
        resolve_visual(record, "UI-000010")
    record["roots"][0]["enabled"] = True
    record["screenshots"][0]["sha256"] = "old"
    with pytest.raises(ValueError, match="Stale"):
        resolve_visual(record, "UI-000010")

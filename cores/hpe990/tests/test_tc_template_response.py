"""Compact MCP receipts preserve complete persisted catalog evidence."""

import pytest

from cores.hpe990.mcp.tools import scenarios


@pytest.mark.parametrize("summary_only", [False, True])
def test_template_receipt_limits_transfer_without_limiting_catalog(monkeypatch, summary_only):
    report = {
        "drafts": [{"ui_id": "UI-000001", "evidence": ["inventory.json"]}],
        "templates": {"number": {"steps": []}},
        "element_count": 1,
        "json": "catalog.json",
        "html": "review.html",
        "bdd_executed": False,
    }
    calls = []

    def generate(session, ui_ids):
        calls.append((session, ui_ids))
        return report

    monkeypatch.setattr(scenarios, "template_catalog", generate)
    receipt = scenarios.hpe990_tc_templates("session", summary_only=summary_only)
    assert calls == [("session", None)]
    assert receipt["element_count"] == 1
    assert receipt["json"] == "catalog.json" and receipt["html"] == "review.html"
    assert receipt["bdd_executed"] is False
    assert ("drafts" in receipt) is not summary_only
    assert ("templates" in receipt) is not summary_only
    assert report["drafts"][0]["evidence"] == ["inventory.json"]

"""Fail closed on incomplete or tampered UI evidence and cross-session paths."""

import hashlib
import json

import pytest
from PIL import Image

from cores.hpe990.functions import collection_audit as audit


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(audit.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    directory = tmp_path / "ui" / "11111111111111111111111111111111" / "capture"
    directory.mkdir(parents=True)
    image = directory / "screen.png"
    Image.new("RGB", (4, 4), "white").save(image)
    record = {
        "session_id": "11111111111111111111111111111111",
        "ui_registry": {"elements": [{"ui_id": "UI-1"}]},
        "nodes": [{"ui_id": "UI-1"}],
        "roots": [{"ui_id": "UI-1", "hwnd": 1, "visible": True}],
        "screenshots": [
            {
                "hwnd": 1,
                "path": str(image),
                "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            }
        ],
    }
    path = directory / "inventory.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path, image, record


def test_evidence_pass_is_not_whole_application_pass(snapshot):
    path, _, _ = snapshot
    result = audit.audit_collection("11111111111111111111111111111111", [str(path), str(path)])
    assert result["inventory_count"] == 1
    assert result["evidence_verdict"] == "PASS"
    assert not result["whole_application_complete"]


def test_tampered_png_fails(snapshot):
    path, image, _ = snapshot
    image.write_bytes(b"tampered")
    result = audit.audit_collection("11111111111111111111111111111111", [str(path)])
    assert result["evidence_verdict"] == "FAIL"
    assert result["errors"][0]["reason"] == "image_hash_mismatch"


def test_missing_identity_and_screenshot_fail(snapshot):
    path, _, record = snapshot
    record["nodes"] = [{}]
    record["screenshots"] = []
    path.write_text(json.dumps(record), encoding="utf-8")
    result = audit.audit_collection("11111111111111111111111111111111", [str(path)])
    assert {e["reason"] for e in result["errors"]} == {"missing_ui_id", "missing_screen_capture"}


def test_reject_foreign_session_evidence(snapshot):
    path, _, _ = snapshot
    with pytest.raises(ValueError, match="specified session"):
        audit.audit_collection("22222222222222222222222222222222", [str(path)])


def test_expected_screen_requires_active_evidence(snapshot):
    path, _, record = snapshot
    record["roots"][0].update(name="Setup", enabled=False)
    path.write_text(json.dumps(record), encoding="utf-8")
    result = audit.audit_collection("11111111111111111111111111111111", [str(path)], ["Setup"])
    assert result["evidence_verdict"] == "FAIL"
    assert result["errors"] == [{"reason": "missing_expected_screen", "screen": "Setup"}]
    record["roots"][0]["enabled"] = True
    path.write_text(json.dumps(record), encoding="utf-8")
    assert (
        audit.audit_collection("11111111111111111111111111111111", [str(path)], ["Setup"])[
            "evidence_verdict"
        ]
        == "PASS"
    )

"""Fail-closed registration guards before any real desktop input is dispatched."""

import json
import shutil

import pytest

from cores.common.functions import run_family_bdd as gate
from cores.common.paths import D_ROOT


@pytest.fixture
def registry_copy(tmp_path, monkeypatch):
    source = D_ROOT / "cores/hpe990"
    destination = tmp_path / "cores/hpe990"
    for relative in ("tests/bdd", "configs"):
        shutil.copytree(source / relative, destination / relative)
    monkeypatch.setattr(gate, "D_ROOT", tmp_path)
    return destination


def test_duplicate_registration_fails_before_input(registry_copy):
    path = registry_copy / "configs/one_shot_bdd.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["features"].append(config["features"][0])
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate"):
        gate.bdd_registry("hpe990")


def test_unregistered_feature_fails_before_input(registry_copy):
    extra = registry_copy / "tests/bdd/scenarios/features/unregistered.feature"
    extra.write_text("Feature: Unregistered\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Unregistered"):
        gate.bdd_registry("hpe990")


def test_missing_binding_fails_before_input(registry_copy):
    (registry_copy / "tests/bdd/scenarios/test_bdd_ram.py").unlink()
    with pytest.raises(RuntimeError, match="missing"):
        gate.bdd_registry("hpe990")


def test_desktop_input_is_never_implicitly_authorized():
    with pytest.raises(PermissionError, match="allow-desktop-input"):
        gate.run_family_bdd("hpe990")

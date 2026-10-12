"""Validate key contracts before any desktop interaction."""

from types import SimpleNamespace

import pytest

from cores.hpe990.functions.ui_keyboard import parse_keys


def test_chords_function_keys_and_sequences():
    assert parse_keys(["Ctrl+A", "Home", "Shift+End", "F24", "Alt+F4", "Win+Right"]) == [
        [0x11, 0x41],
        [0x24],
        [0x10, 0x23],
        [0x87],
        [0x12, 0x73],
        [0x5B, 0x27],
    ]


@pytest.mark.parametrize(
    "keys",
    [
        [],
        "Ctrl+A",
        [None],
        ["Ctrl"],
        ["Ctrl+Ctrl+A"],
        ["A+B"],
        ["F25"],
        ["Unknown"],
        ["Ctrl+"],
        ["A"] * 33,
    ],
)
def test_invalid_keys_rejected(keys):
    with pytest.raises(ValueError):
        parse_keys(keys)


def input_fixture(monkeypatch, tmp_path, enabled=True):
    from cores.hpe990.functions import ui_keyboard as module

    binary = tmp_path / "input.exe"
    binary.touch()
    node = {
        "ui_id": "UI-000001",
        "hwnd": 1,
        "pid": 10,
        "parent": 0,
        "visible": True,
        "enabled": enabled,
    }
    monkeypatch.setattr(
        module,
        "hpe990_folders",
        SimpleNamespace(
            F_HPE990_INPUT=binary, D_HPE990_RUNTIME=tmp_path, D_HPE990_EVIDENCE=tmp_path
        ),
    )
    monkeypatch.setattr(module, "session_guard", lambda *args: None)
    monkeypatch.setattr(module, "start_ram", lambda *args: None)
    monkeypatch.setattr(
        module, "collect_ui", lambda *args, **kwargs: {"nodes": [node], "evidence": "snapshot"}
    )
    monkeypatch.setattr(module, "_native_node", lambda *args: node)
    monkeypatch.setattr(module, "action_marker", lambda *args: None)
    return module


def test_activation_failure_does_not_release_user_keys(monkeypatch, tmp_path):
    module = input_fixture(monkeypatch, tmp_path)
    calls = []

    def backend(kind, request):
        calls.append((kind, request))
        return {
            "receipt": {
                "ok": False,
                "error": "Cannot establish target foreground",
                "key_downs_delivered": 0,
                "residual_keys": 0,
            }
        }

    monkeypatch.setattr(module, "request_backend", backend)
    with pytest.raises(RuntimeError, match="activation_required"):
        module.activate_ui("session", "UI-000001")
    assert len(calls) == 1, "No release helper when no worker-owned keys exist"
    assert len(list(tmp_path.glob("**/receipt.json"))) == 1


def test_disabled_target_rejected_before_backend(monkeypatch, tmp_path):
    module = input_fixture(monkeypatch, tmp_path, enabled=False)
    monkeypatch.setattr(
        module, "request_backend", lambda *args: pytest.fail("No input to disabled target")
    )
    with pytest.raises(ValueError, match="disabled"):
        module.activate_ui("session", "UI-000001")


@pytest.mark.parametrize("field", ["pid", "hwnd"])
def test_changed_native_identity_rejected_before_input(monkeypatch, tmp_path, field):
    module = input_fixture(monkeypatch, tmp_path)
    original = module._native_node(1)
    monkeypatch.setattr(module, "_native_node", lambda *args: {**original, field: 999})
    monkeypatch.setattr(
        module, "request_backend", lambda *args: pytest.fail("No input to changed identity")
    )
    with pytest.raises(ValueError, match="changed"):
        module.activate_ui("session", "UI-000001")

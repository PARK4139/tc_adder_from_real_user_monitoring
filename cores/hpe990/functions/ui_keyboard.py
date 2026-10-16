"""UI-ID scoped key sequences, with Rust delivery and Real Activity Monitoring receipts."""

import json
import uuid

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.backend import request_backend
from cores.hpe990.functions.monitoring import action_marker, ram_status, session_guard, start_ram
from cores.hpe990.functions.ui import _native_node, collect_ui
from cores.hpe990.functions.ui_drag import resolve_drag_node

MODIFIERS = {"ctrl": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B}
KEYS = {
    "enter": 0x0D,
    "escape": 0x1B,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}
KEYS.update({chr(i).lower(): i for i in range(ord("A"), ord("Z") + 1)})
KEYS.update({str(i): ord(str(i)) for i in range(10)})
KEYS.update({f"f{i}": 0x6F + i for i in range(1, 25)})


def parse_keys(keys):
    if not isinstance(keys, list) or not 1 <= len(keys) <= 32:
        raise ValueError("keys must contain 1..32 key chords")
    result = []
    for chord in keys:
        if not isinstance(chord, str):
            raise ValueError("Each key chord must be text")
        parts = [part.strip().lower() for part in chord.split("+")]
        if (
            parts[-1] not in KEYS
            or any(part not in MODIFIERS for part in parts[:-1])
            or len(parts) != len(set(parts))
        ):
            raise ValueError(f"Unknown key or invalid chord: {chord}")
        result.append([MODIFIERS[part] for part in parts[:-1]] + [KEYS[parts[-1]]])
    return result


def keys_ui(session_id, ui_id, keys):
    sequence = parse_keys(keys)
    return _input_ui(session_id, ui_id, sequence, keys, "keys")


def activate_ui(session_id, ui_id):
    """Activate one observed target without sending application keys."""
    return _input_ui(session_id, ui_id, [], [], "activate")


def minimize_ui(session_id, ui_id):
    return _input_ui(session_id, ui_id, [], [], "minimize")


def _input_ui(session_id, ui_id, sequence, keys, operation):
    session_guard(session_id)
    binary = hpe990_folders.F_HPE990_INPUT
    if not binary.is_file():
        raise FileNotFoundError(f"Build the Rust input worker first: {binary}")
    with FileLock(str(hpe990_folders.D_HPE990_RUNTIME / "keyboard.lock"), timeout=1):
        start_ram(session_id)
        before = collect_ui(
            session_id, screenshots=False, accessibility_backend="none", refresh_templates=False
        )
        node = resolve_drag_node(before, ui_id)
        session_guard(session_id)
        fresh = _native_node(node["hwnd"])
        if fresh != {k: v for k, v in node.items() if k in fresh}:
            raise ValueError("Keyboard target changed during collection")
        action_id = uuid.uuid4().hex
        issue_id = "f182f260" if operation == "keys" else "fea44e48"
        directory = hpe990_folders.D_HPE990_EVIDENCE / issue_id / session_id / action_id
        directory.mkdir(parents=True)
        ownership = directory / "held-keys"
        ownership.mkdir()
        request = {
            "operation": operation,
            "pid": node["pid"],
            "source": node,
            "keys": sequence,
            "held_keys_directory": str(ownership),
        }
        path = directory / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        details = {"action": operation, "ui_id": ui_id, "keys": keys, "before": before["evidence"]}
        action_marker(session_id, action_id, "requested", details)
        try:
            receipt = request_backend("input", {"request": str(path)})["receipt"]
            receipt["activation_required"] = not receipt["ok"] and any(
                term in (receipt.get("error") or "").lower()
                for term in ("foreground", "focus", "activation input queue", "minimized")
            )
            (directory / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            if not receipt["ok"]:
                raise RuntimeError(receipt)
            after = collect_ui(
                session_id, screenshots=False, accessibility_backend="none", refresh_templates=False
            )
            result = {
                **details,
                "action_id": action_id,
                "receipt": receipt,
                "after": after["evidence"],
                "ram_active": ram_status(session_id)["active"],
                "scope": "Input delivered; application behavior requires separate validation",
            }
            action_marker(session_id, action_id, "observed", result)
            (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
            return result
        except Exception as error:
            # A forcibly stopped Rust process cannot run Drop. Release only its validated keys.
            cleanup_code = None
            owned = [int(p.stem) for p in ownership.glob("*.held")]
            if owned:
                release = directory / "release.json"
                release.write_text(
                    json.dumps({**request, "operation": "release_keys", "keys": [owned]}),
                    encoding="utf-8",
                )
                cleanup = request_backend("input", {"request": str(release)})["receipt"]
                cleanup_code = 0 if cleanup["ok"] else 1
            action_marker(
                session_id,
                action_id,
                "failed",
                {**details, "error": str(error), "cleanup_returncode": cleanup_code},
            )
            raise

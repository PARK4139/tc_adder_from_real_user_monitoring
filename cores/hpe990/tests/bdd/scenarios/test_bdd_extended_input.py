"""Live OCR/keyboard acceptance through public MCP; preserve app values and RAM."""

import json
import os
import time
import uuid
from pathlib import Path

import pytest
from pytest_bdd import given, scenario, then, when

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.tests.bdd.scenarios.test_bdd_ram import MCPDesktop

pytestmark = pytest.mark.integration


def visible(record, name):
    return [n for n in record["nodes"] if n["name"] == name and n["visible"] and n["enabled"]]


def wait_visible(client, session, name):
    deadline = time.monotonic() + 10
    while True:
        record = client.call(
            "hpe990_ui_collect", session_id=session, screenshots=False, accessibility_backend="none"
        )
        if visible(record, name):
            return record
        if time.monotonic() >= deadline:
            raise AssertionError(f"Timed out waiting for {name}")
        time.sleep(0.1)


def cancel_preferences(client, session):
    record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
    roots = visible(record, "Preferences")
    assert len(roots) == 1
    client.call("hpe990_ui_activate", session_id=session, ui_id=roots[0]["ui_id"])
    candidates = [
        e
        for e in record["visual"]["elements"]
        if e.get("name", "").lower() == "cancel" and e["root_hwnd"] == roots[0]["hwnd"]
    ]
    assert len(candidates) == 1, "Cancel must be uniquely observed, not guessed"
    client.call("hpe990_ui_control_visual", session_id=session, ui_id=candidates[0]["ui_id"])
    return wait_visible(client, session, "Setup")


@pytest.fixture
def extended_desktop():
    directory = (
        Path(
            os.environ.get(
                "HPE990_BDD_EVIDENCE",
                str(hpe990_folders.D_HPE990_EVIDENCE / "f182f260" / uuid.uuid4().hex),
            )
        )
        / "extended-input"
    )
    directory.mkdir(parents=True, exist_ok=True)
    client = MCPDesktop(directory)
    try:
        yield client
    finally:
        try:
            session = client.state.get("session_id")
            if session:
                record = client.call(
                    "hpe990_ui_collect",
                    session_id=session,
                    screenshots=False,
                    accessibility_backend="none",
                )
                preferences = visible(record, "Preferences")
                if preferences:
                    cancel_preferences(client, session)
                setup = client.state.get("setup")
                if setup:
                    client.call(
                        "hpe990_window_geometry",
                        session_id=session,
                        hwnd=setup["hwnd"],
                        rect=setup["rect"],
                    )
        finally:
            client.close()


@scenario(
    "features/extended_input.feature",
    "OCR Preferences entry and reversible keyboard tab navigation three times",
)
def test_extended_input():
    pass


@given("Setup is open with an unchanged owned Emulator and active RAM")
def prepare(extended_desktop):
    client = extended_desktop
    app = client.call("hpe990_status")
    assert app["running"] and app["owned"]
    session = app["session_id"]
    client.state["session_id"] = session
    record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
    setup = visible(record, "Setup")
    if not setup and visible(record, "Preferences"):
        record = cancel_preferences(client, session)
        setup = visible(record, "Setup")
    assert len(setup) == 1, "Start this acceptance at the observed Setup screen"
    client.state["setup"] = setup[0]
    assert client.call("hpe990_ram_start", session_id=session)["active"]


@when("I enter Preferences through its recollected OCR label and navigate tabs three times")
def exercise(extended_desktop):
    client = extended_desktop
    session = client.state["session_id"]
    results = []
    client.state["results"] = results
    for cycle in range(3):
        record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
        setup = visible(record, "Setup")[0]
        target = [
            e
            for e in record["visual"]["elements"]
            if e.get("name") == "Preferences" and e["root_hwnd"] == setup["hwnd"]
        ]
        assert len(target) == 1 and target[0].get("hwnd") is None
        # F24 is tested as delivery only; no HPE990 F24 feature is inferred.
        receipt = client.call(
            "hpe990_ui_keys", session_id=session, ui_id=setup["ui_id"], keys=["F24"]
        )
        assert receipt["receipt"]["residual_keys"] == 0
        if cycle:
            original = client.state["setup"]["rect"]
            moved = [v + (cycle if i in (0, 2) else 0) for i, v in enumerate(original)]
            assert (
                client.call(
                    "hpe990_window_geometry", session_id=session, hwnd=setup["hwnd"], rect=moved
                )["actual_rect"]
                == moved
            )
        opened = client.call(
            "hpe990_ui_control_visual", session_id=session, ui_id=target[0]["ui_id"]
        )
        record = json.loads(Path(opened["after"]).read_text(encoding="utf-8"))
        if not visible(record, "Preferences"):
            record = wait_visible(client, session, "Preferences")
        preferences = visible(record, "Preferences")
        assert len(preferences) == 1 and visible(record, "tab_general")
        bar = visible(record, "qt_tabwidget_tabbar")
        assert len(bar) == 1
        transitions = []
        for keys, page in (
            (["Ctrl+Tab"], "tab_layout"),
            (["Ctrl+Shift+Tab"], "tab_general"),
            (["Right"], "tab_layout"),
            (["Left"], "tab_general"),
        ):
            action = client.call(
                "hpe990_ui_keys", session_id=session, ui_id=bar[0]["ui_id"], keys=keys
            )
            after = wait_visible(client, session, page)
            assert visible(after, page), f"Expected {page} after {keys}"
            assert action["ram_active"] and action["receipt"]["residual_keys"] == 0
            transitions.append(action)
        cancel_preferences(client, session)
        results.append(
            {"cycle": cycle, "visual": opened, "transitions": transitions, "function_key": receipt}
        )


@then("every observed tab transition matches the requested keyboard input and RAM remains active")
def verify(extended_desktop):
    client = extended_desktop
    assert len(client.state["results"]) == 3
    assert client.call("hpe990_ram_status", session_id=client.state["session_id"])["active"]
    (client.evidence / "acceptance.json").write_text(
        json.dumps(
            {"verdict": "PASS", "results": client.state["results"]}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )

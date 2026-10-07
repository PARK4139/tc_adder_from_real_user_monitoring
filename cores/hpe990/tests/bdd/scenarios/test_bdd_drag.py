"""Live scrollbar BDD through public MCP; preserve the user's existing session and RAM."""

import json
import os
import uuid
from pathlib import Path

import pytest
from filelock import FileLock
from pytest_bdd import given, scenario, then, when

from cores.common.paths import D_TEMP
from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.operations import OPERATION_TO_TOOL
from cores.hpe990.tests.bdd.scenarios.test_bdd_ram import MCPDesktop

pytestmark = pytest.mark.integration


@pytest.fixture
def drag_desktop():
    directory = (
        Path(
            os.environ.get(
                "HPE990_BDD_EVIDENCE",
                str(hpe990_folders.D_HPE990_EVIDENCE / "04be9d05" / uuid.uuid4().hex),
            )
        )
        / "test_ui_drag"
    )
    directory.mkdir(parents=True, exist_ok=True)
    lock = D_TEMP / "common/desktop-input.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(lock), timeout=1):
        client = MCPDesktop(directory)
        try:
            yield client
        finally:
            try:
                restore = client.state.get("restore_tab")
                if restore:
                    client.call(
                        "hpe990_ui_control",
                        session_id=client.state["session_id"],
                        name="qt_tabwidget_tabbar",
                        root_hwnd=restore["root_hwnd"],
                        point_fraction=[restore["fraction"], 0.5],
                    )
                    client.state["original_tab_restored"] = restore["name"]
            finally:
                client.close()


@scenario(
    "features/drag.feature", "General scrollbar drag and reverse restore the viewport three times"
)
def test_general_scrollbar_drag():
    pass


def snapshot_top(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = [
        n
        for n in record["nodes"]
        if n["name"] == "scrollAreaWidgetContents_general" and n["visible"]
    ]
    assert len(nodes) == 1
    return nodes[0]["rect"][1]


@given("General is open at its initial scroll position with RAM active")
def general_open(drag_desktop):
    client = drag_desktop
    app = client.call("hpe990_status")
    if not app["running"]:
        app = client.call("hpe990_launch")
    session = app["session_id"]
    client.state["session_id"] = session
    record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
    preferences = [r for r in record["roots"] if r["name"] == "Preferences" and r["visible"]]
    if not preferences:
        setups = [
            r for r in record["roots"] if r["name"] == "Setup" and r["visible"] and r["enabled"]
        ]
        if not setups:
            client.call("hpe990_ui_control", session_id=session, name="pushButton_setting")
        client.call("hpe990_ui_control", session_id=session, name="pushButton_preferences")
        record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
        preferences = [r for r in record["roots"] if r["name"] == "Preferences" and r["visible"]]
    assert len(preferences) == 1 and preferences[0]["enabled"]
    client.state["preferences_root"] = preferences[0]["hwnd"]
    page_names = [
        "tab_general",
        "tab_layout",
        "tab_edging",
        "tab_digitalPattern",
        "tab_holeEditor",
        "tab_frameFitting",
        "tab_port",
    ]
    pages = [n for n in record["nodes"] if n["name"] in page_names and n["visible"]]
    assert len(pages) == 1, "Identify the selected Preferences page before changing it"
    if pages[0]["name"] != "tab_general":
        client.state["restore_tab"] = {
            "name": pages[0]["name"],
            "root_hwnd": preferences[0]["hwnd"],
            "fraction": (page_names.index(pages[0]["name"]) + 0.5) / len(page_names),
        }
        client.call(
            "hpe990_ui_control",
            session_id=session,
            name="qt_tabwidget_tabbar",
            root_hwnd=preferences[0]["hwnd"],
            point_fraction=[0.5 / len(page_names), 0.5],
        )
        record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
    by_handle = {n["hwnd"]: n for n in record["nodes"]}
    containers = [
        n for n in record["nodes"] if n["name"] == "qt_scrollarea_vcontainer" and n["visible"]
    ]
    assert len(containers) == 1
    bars = [n for n in record["nodes"] if n["parent"] == containers[0]["hwnd"] and n["visible"]]
    assert len(bars) == 1
    viewport = next(
        n for n in record["nodes"] if n["name"] == "qt_scrollarea_viewport" and n["visible"]
    )
    if snapshot_top(record["evidence"]) != viewport["rect"][1]:
        client.state["preparation_scroll_top"] = True
        client.call(
            "hpe990_ui_control",
            session_id=session,
            name="qt_scrollarea_viewport",
            hwnd=viewport["hwnd"],
            root_hwnd=preferences[0]["hwnd"],
            action="scroll_up",
        )
        record = client.call("hpe990_ui_collect", session_id=session, accessibility_backend="none")
    assert snapshot_top(record["evidence"]) == viewport["rect"][1]
    assert by_handle[bars[0]["parent"]]["enabled"]
    client.state["bar"] = bars[0]
    client.state["initial_top"] = viewport["rect"][1]
    monitor = client.call("hpe990_ram_start", session_id=session)
    assert monitor["active"]
    client.state["ram_directory"] = monitor["directory"]
    discovery = json.loads((client.evidence / "discovery.json").read_text())
    assert {tool["name"] for tool in discovery} == set(OPERATION_TO_TOOL.values())


@when("I drag the native scrollbar and reverse it three times through MCP")
def repeated_drag(drag_desktop):
    client = drag_desktop
    session = client.state["session_id"]
    client.state["drags"] = []
    for _ in range(3):
        forward = client.call(
            "hpe990_ui_drag",
            session_id=session,
            source_ui_id=client.state["bar"]["ui_id"],
            start_fraction=[0.5, 0.3],
            end_fraction=[0.5, 0.55],
            duration_ms=500,
        )
        try:
            client.state["drags"].append({"forward": forward})
        finally:
            reverse = client.call(
                "hpe990_ui_drag",
                session_id=session,
                source_ui_id=client.state["bar"]["ui_id"],
                start_fraction=[0.5, 0.55],
                end_fraction=[0.5, 0.3],
                duration_ms=500,
            )
            client.state["drags"][-1]["reverse"] = reverse


@then("each drag scrolls General and each reverse restores its initial position")
def verify_results(drag_desktop):
    client = drag_desktop
    for pair in client.state["drags"]:
        forward, reverse = pair["forward"], pair["reverse"]
        assert snapshot_top(forward["after"]) < snapshot_top(forward["before"])
        assert snapshot_top(reverse["after"]) == client.state["initial_top"]
        for result in pair.values():
            assert result["worker"]["button_release_posted"] and result["ram_active"]
            assert result["ram_directory"] == client.state["ram_directory"]
            assert Path(result["receipt"]).is_file()
    client.state["drag_application_result"] = "PASS"


@then("invalid drag targets and parameters are rejected while RAM stays active")
def rejected_inputs(drag_desktop):
    client = drag_desktop
    session = client.state["session_id"]
    for ui_id, duration in [("UI-999999999", 500), (client.state["bar"]["ui_id"], 0)]:
        with pytest.raises(RuntimeError):
            client.call(
                "hpe990_ui_drag",
                session_id=session,
                source_ui_id=ui_id,
                start_fraction=[0.5, 0.3],
                end_fraction=[0.5, 0.55],
                duration_ms=duration,
            )
    monitor = client.call("hpe990_ram_status", session_id=session)
    assert monitor["active"] and monitor["directory"] == client.state["ram_directory"]
    client.state["whole_application_complete"] = False

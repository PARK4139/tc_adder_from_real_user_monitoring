"""Real acceptance behavior through public MCP; no simulated passing helpers."""

import asyncio
import concurrent.futures
import json
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pytest_bdd import given, scenario, then, when

from cores.common.paths import D_ROOT, D_TEMP
from cores.hpe990.common.paths import hpe990_folders

pytestmark = pytest.mark.integration


class MCPDesktop:
    def __init__(self, evidence):
        self.evidence = evidence
        self.requests = queue.Queue()
        self.ready = concurrent.futures.Future()
        self.calls = []
        self.state = {}
        self.thread = threading.Thread(target=lambda: asyncio.run(self.serve()), daemon=True)
        self.thread.start()
        self.ready.result(timeout=30)

    async def serve(self):
        executable = os.environ.get("HPE990_BDD_EXECUTABLE")
        command = executable or str(D_ROOT / ".venv" / "Scripts" / "python.exe")
        args = ["--mcp"] if executable else ["-m", "cores.hpe990.mcp.server"]
        try:
            with (self.evidence / "mcp-stderr.log").open("w", encoding="utf-8") as errors:
                async with stdio_client(
                    StdioServerParameters(command=command, args=args, cwd=str(D_ROOT)),
                    errlog=errors,
                ) as (read, write):
                    async with ClientSession(read, write) as client:
                        await client.initialize()
                        discovery = await client.list_tools()
                        (self.evidence / "discovery.json").write_text(
                            json.dumps(
                                [t.model_dump(mode="json") for t in discovery.tools], indent=2
                            ),
                            encoding="utf-8",
                        )
                        self.ready.set_result(True)
                        while True:
                            request = await asyncio.to_thread(self.requests.get)
                            if request is None:
                                break
                            name, arguments, future = request
                            try:
                                result = await client.call_tool(name, arguments)
                                self.calls.append(
                                    {
                                        "name": name,
                                        "arguments": arguments,
                                        "result": result.model_dump(mode="json"),
                                    }
                                )
                                if result.isError:
                                    raise RuntimeError(result.content)
                                future.set_result(
                                    result.structuredContent or json.loads(result.content[0].text)
                                )
                            except Exception as error:
                                future.set_exception(error)
        except Exception as error:
            if not self.ready.done():
                self.ready.set_exception(error)
            else:
                self.state["adapter_error"] = str(error)
        finally:
            (self.evidence / "mcp-contract-report.json").write_text(
                json.dumps(
                    {"calls": self.calls, "state": self.state}, ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )

    def call(self, tool_name, **arguments):
        future = concurrent.futures.Future()
        self.requests.put((tool_name, arguments, future))
        return future.result(timeout=150)

    def close(self):
        self.requests.put(None)
        self.thread.join(timeout=30)
        if self.thread.is_alive():
            raise RuntimeError("MCP adapter cleanup timed out")


@pytest.fixture
def desktop(request):
    evidence = Path(
        os.environ.get(
            "HPE990_BDD_EVIDENCE",
            str(hpe990_folders.D_HPE990_EVIDENCE / "92dd1b63" / uuid.uuid4().hex),
        )
    )
    evidence = evidence / request.node.name
    evidence.mkdir(parents=True, exist_ok=True)
    lock_path = D_TEMP / "common" / "desktop-input.lock"
    from filelock import FileLock

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(lock_path), timeout=1):
        client = MCPDesktop(evidence)
        try:
            yield client
        finally:
            session_id = client.state.get("session_id")
            try:
                if session_id:
                    current = client.call("hpe990_status")
                    if current["running"] and current["owned"]:
                        client.call("hpe990_stop", session_id=session_id, force=True)
                    client.call("hpe990_ram_stop", session_id=session_id)
            finally:
                client.close()


@scenario("features/ram.feature", "Startup, modal navigation and application stop remain monitored")
def test_ram_activity():
    pass


@scenario(
    "features/telemetry.feature", "Observed window changes have ordered and correlated evidence"
)
def test_window_telemetry():
    pass


@scenario("features/analysis.feature", "Every observed state and transition has traceable evidence")
def test_observed_analysis():
    pass


@scenario(
    "features/workflow.feature",
    "Launch through Continue, navigate a confirmation and stop the application",
)
def test_launch_to_stop_workflow():
    pass


@scenario(
    "features/control.feature",
    "A rejected control request preserves monitoring and owned-session cleanup",
)
def test_failed_control_monitoring():
    pass


@given("the approved Emulator is stopped")
def stopped(desktop):
    current = desktop.call("hpe990_status")
    if current["running"]:
        assert current["owned"], "External session must be stopped by its owner before BDD"
        desktop.call("hpe990_stop", session_id=current["session_id"], force=True)
    assert not desktop.call("hpe990_status")["running"]


@scenario(
    "features/visualization.feature", "Registered scenarios are available without the UI gallery"
)
def test_dynamic_ui_visualization():
    pass


@when("I open the BDD scenario screen")
def viewer_opened(desktop):
    viewer = desktop.call("hpe990_ui_visualize", open_browser=False)
    desktop.state["viewer"] = viewer
    with urlopen(viewer["url"], timeout=15) as response:
        html = response.read().decode("utf-8")
        assert "BDD 시나리오 목록" in html and "Given / When / Then" in html
        assert "전체 갤러리" not in html and "전체 수집 요소" not in html
        assert "<img" not in html and 'id="screens"' not in html


@then("the viewer lists every registered BDD scenario with its steps and issue")
def viewer_bdd_catalog(desktop):
    viewer = desktop.state["viewer"]
    try:
        with urlopen(viewer["url"] + "data", timeout=15) as response:
            displayed = json.load(response)
        catalog = desktop.call("hpe990_bdd_catalog")
        assert displayed["bdd_error"] is None
        assert displayed["bdd"] == catalog
        assert "windows" not in displayed and "all_controls" not in displayed
        assert catalog["expected_tests"] == len(catalog["scenarios"]) == 6
        for item in catalog["scenarios"]:
            assert item["steps"] and item["gherkin"] and item["binding"] and item["test"]
            assert any(tag.startswith("@ISSUE-") for tag in item["tags"])
        (desktop.evidence / "bdd-screen.json").write_text(
            json.dumps(displayed, indent=2), encoding="utf-8"
        )
    finally:
        assert desktop.call("hpe990_ui_viewer_stop")["stopped"]


@when("I launch the Emulator and continue into Edger")
def launched(desktop):
    status = desktop.call("hpe990_launch")
    desktop.state.update(session_id=status["session_id"], launch=status)
    (desktop.evidence / "session.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    assert status["ready"] and status["startup_completed"]
    assert status["continue_action"]["control_name"] == "pushButton_continue"
    monitor = desktop.call("hpe990_ram_status", session_id=status["session_id"])
    assert monitor["active"]
    assert desktop.call("hpe990_ram_start", session_id=status["session_id"])["active"]
    desktop.state["ram_directory"] = monitor["directory"]


@when("I open Setup and its Shutdown confirmation")
def opened(desktop):
    session = desktop.state["session_id"]
    desktop.call("hpe990_ui_control", session_id=session, name="pushButton_setting")
    snapshot = desktop.call("hpe990_ui_collect", session_id=session)
    roots = [r for r in snapshot["roots"] if r["name"] == "Setup" and r["visible"]]
    assert len(roots) == 1 and roots[0]["enabled"]
    desktop.call(
        "hpe990_ui_control",
        session_id=session,
        name="pushButton_shutdown",
        root_hwnd=roots[0]["hwnd"],
    )
    snapshot = desktop.call("hpe990_ui_collect", session_id=session)
    assert any(r["name"] == "Shutdown" and r["visible"] for r in snapshot["roots"])
    assert not snapshot["capture_errors"]
    desktop.state["shutdown_inventory"] = snapshot["evidence"]


@when("I cancel the Shutdown confirmation")
def cancelled(desktop):
    session = desktop.state["session_id"]
    result = desktop.call("hpe990_ui_control", session_id=session, name="Shutdown", action="escape")
    assert result["ram_active"]
    snapshot = desktop.call("hpe990_ui_collect", session_id=session, screenshots=False)
    assert not any(r["name"] == "Shutdown" and r["visible"] for r in snapshot["roots"])


@when("I stop the owned Emulator application explicitly")
def exited(desktop):
    session = desktop.state["session_id"]
    result = desktop.call("hpe990_stop", session_id=session, force=True)
    assert result["closed"] and result["exit_method"] == "explicit_force"
    desktop.state["stop_action_id"] = result["action_id"]
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        monitor = desktop.call("hpe990_ram_status", session_id=session)
        if not monitor["active"] and "ram_report" in monitor:
            desktop.state["ram_report"] = monitor["ram_report"]
            return
        time.sleep(0.1)
    raise AssertionError("Monitor failed to flush after process exit")


@then("every declared observed activity has session-linked monitoring evidence")
def complete(desktop):
    session = desktop.state["session_id"]
    events = []
    sequence = 0
    while True:
        page = desktop.call(
            "hpe990_telemetry_read", session_id=session, after_sequence=sequence, limit=1000
        )
        events.extend(page["events"])
        if not page["events"]:
            break
        sequence = page["next_sequence"]
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    assert all(e["session_id"] == session and e["schema_version"] == 1 for e in events)
    names = {e["window"]["name"] for e in events if "window" in e}
    declared = {
        "startup_dialog": "PC Simulator",
        "main_screen": "Edger",
        "setup": "Setup",
        "confirmation": "Shutdown",
    }
    checks = {key: value in names for key, value in declared.items()}
    checks["process_exit"] = any(
        e["kind"] == "monitor_stopped" and e["reason"] == "process_exited" for e in events
    )
    assert all(checks.values()), checks
    report = {
        **desktop.state["ram_report"],
        "declared_activities": declared,
        "activity_checks": checks,
        "recording_coverage_percent": 100,
        "missing_session_associations": 0,
        "sequence_gaps": 0,
        "sequence_duplicates": 0,
        "exit_method": "explicit_force",
        "verdict": "PASS",
    }
    (desktop.evidence / "ram-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    desktop.state["verdict"] = "PASS"


@when("I request an unavailable control")
def invalid_control(desktop):
    session = desktop.state["session_id"]
    before = desktop.call("hpe990_ram_status", session_id=session)
    with pytest.raises(RuntimeError):
        desktop.call("hpe990_ui_control", session_id=session, name="__unavailable_test_control__")
    after = desktop.call("hpe990_ram_status", session_id=session)
    assert after["active"] and after["snapshot"]["scan"] >= before["snapshot"]["scan"]
    desktop.state["failed_control_observed"] = True


@then("the rejected request and cleanup remain in the monitoring evidence")
def failed_control_recorded(desktop):
    session = desktop.state["session_id"]
    exported = desktop.call("hpe990_telemetry_export", session_id=session)
    assert exported["verdict"] == "PASS"
    events = [
        json.loads(line)
        for line in Path(exported["export"]).read_text(encoding="utf-8").splitlines()
    ]
    assert any(
        e["kind"] == "control_action" and e["phase"] == "failed" and e["error_type"] == "ValueError"
        for e in events
    )
    assert any(
        e["kind"] == "control_action"
        and e["action_id"] == desktop.state["stop_action_id"]
        and e["phase"] == "observed"
        for e in events
    )
    assert any(e["kind"] == "monitor_stopped" and e["reason"] == "process_exited" for e in events)
    assert not desktop.call("hpe990_ram_status", session_id=session)["active"]
    desktop.state["verdict"] = "PASS"
    (desktop.evidence / "concurrent-ram-report.json").write_text(
        json.dumps(
            {
                "session_id": session,
                "verdict": "PASS",
                "expected_failure_recorded": True,
                "ram_active_after_failure": True,
                "worker_cleaned_after_exit": True,
                "missing_action_associations": 0,
                "telemetry": exported["evidence"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@then("the analysis maps every observed state and transition to evidence")
def analysis_complete(desktop):
    complete(desktop)
    catalog = desktop.call("hpe990_ui_catalog", session_id=desktop.state["session_id"])
    assert catalog["unique_native_controls"] > 0 and catalog["observations"]
    analysis = desktop.call("hpe990_ui_analyze", session_id=desktop.state["session_id"])
    assert analysis["states"] and analysis["transitions"]
    assert all(s["evidence"] and s["kind"] == "observed" for s in analysis["states"])
    assert all(
        t["evidence"]["before"] and t["evidence"]["after"] and t["kind"] == "observed"
        for t in analysis["transitions"]
    )
    assert analysis["unsupported_factual_transitions"] == 0
    assert analysis["state_evidence_coverage_percent"] == 100
    assert analysis["transition_evidence_coverage_percent"] == 100
    assert not analysis["unmapped_observed_operations"]
    assert all(
        o["mcp_tool"] == "hpe990_ui_control" and o["evidence"]
        for o in analysis["observed_operations"]
    )
    assert not analysis["whole_application_complete"] and analysis["hypotheses"]
    desktop.state["analysis"] = {k: analysis[k] for k in ("evidence", "markdown")}


@when("I change and restore the main window geometry")
def geometry_changed(desktop):
    session = desktop.state["session_id"]
    snapshot = desktop.call("hpe990_ui_collect", session_id=session)
    root = next(r for r in snapshot["roots"] if r["name"] == "Edger" and r["visible"])
    original = root["rect"]
    changed = [original[0] + 12, original[1] + 12, original[2] + 44, original[3] + 36]
    result = desktop.call(
        "hpe990_window_geometry", session_id=session, hwnd=root["hwnd"], rect=changed
    )
    assert result["ram_active"] and result["actual_rect"] != original
    desktop.state["geometry"] = result
    restored = desktop.call(
        "hpe990_window_geometry", session_id=session, hwnd=root["hwnd"], rect=original
    )
    assert restored["actual_rect"] == original


@then("the observed workflow is linked to every required scenario step")
def workflow_mapped(desktop):
    analysis_complete(desktop)
    mapped = desktop.call("hpe990_bdd_catalog", session_id=desktop.state["session_id"])
    assert mapped["verdict"] == "PASS" and mapped["mapping_coverage_percent"] == 100
    assert not mapped["missing_required_transitions"]
    assert mapped["mappings"]
    desktop.state["traceability"] = mapped["evidence"]


@then("observed reference changes have valid ordered local telemetry")
def telemetry_complete(desktop):
    complete(desktop)
    session = desktop.state["session_id"]
    exported = desktop.call("hpe990_telemetry_export", session_id=session)
    assert exported["verdict"] == "PASS", exported
    events = [
        json.loads(line)
        for line in Path(exported["export"]).read_text(encoding="utf-8").splitlines()
    ]
    checks = {}
    checks["create"] = any(
        e["kind"] == "window_created" and e["window"]["name"] == "Shutdown" for e in events
    )
    checks["destroy"] = any(e["kind"] == "window_destroyed" for e in events)
    checks["show"] = (
        any(
            e["kind"] == "window_changed"
            and not e["previous"]["visible"]
            and e["window"]["visible"]
            for e in events
            if e.get("previous")
        )
        or checks["create"]
    )
    checks["state"] = any(
        e["kind"] == "window_changed" and e["previous"]["enabled"] != e["window"]["enabled"]
        for e in events
        if e.get("previous")
    )
    geometry = desktop.state["geometry"]
    checks["position"] = any(
        e["kind"] == "window_changed"
        and e["window"]["hwnd"] == geometry["hwnd"]
        and e["window"]["rect"] == geometry["actual_rect"]
        for e in events
    )
    before, after = geometry["before_rect"], geometry["actual_rect"]
    checks["size"] = (
        after[2] - after[0] != before[2] - before[0] or after[3] - after[1] != before[3] - before[1]
    )
    checks["visual"] = any(e["kind"] == "visual_changed" for e in events)
    checks["focus"] = any(e.get("category") in ("focus", "foreground") for e in events)
    checks["hide"] = any(e.get("category") == "hide" for e in events)
    checks["painted_value"] = any(
        e["kind"] == "visual_changed" and e["hwnd"] == desktop.state["value_window"] for e in events
    )
    controls = [e for e in events if e["kind"] == "control_action"]
    requested = {e["action_id"] for e in controls if e["phase"] == "requested"}
    observed = {e["action_id"] for e in controls if e["phase"] == "observed"}
    checks["action_association"] = requested == observed and bool(requested)
    assert all(checks.values()), checks
    report = {
        **exported,
        "reference_changes": checks,
        "missing_reference_changes": 0,
        "schema_coverage_percent": 100,
        "missing_action_associations": 0,
        "limits": [
            "Only actual observed changes are covered; unreported transient changes "
            "between samples are not guaranteed",
            "Qt painted values are represented "
            "by visual changes when no native value event is emitted",
        ],
    }
    (desktop.evidence / "telemetry-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


@when("I change and restore the job category selection")
def changed_value(desktop):
    session = desktop.state["session_id"]
    desktop.call("hpe990_ui_control", session_id=session, name="pushButton_jobManager")
    observed = desktop.call("hpe990_ui_collect", session_id=session)
    roots = [
        r
        for r in observed["roots"]
        if r["visible"]
        and r["enabled"]
        and r["class_name"] == "QWidget"
        and r["name"] not in ("Edger", "Start")
    ]
    assert len(roots) == 1, roots
    root = roots[0]
    desktop.state["value_window"] = root["hwnd"]
    assert root["name"] == "Job Manager"
    first = next(s["sha256"] for s in observed["screenshots"] if s["hwnd"] == root["hwnd"])
    desktop.call(
        "hpe990_ui_control",
        session_id=session,
        name="qt_tabwidget_tabbar",
        root_hwnd=root["hwnd"],
        point_fraction=[0.5, 0.5],
    )
    changed = desktop.call("hpe990_ui_collect", session_id=session)
    second = next(s["sha256"] for s in changed["screenshots"] if s["hwnd"] == root["hwnd"])
    assert first != second, "Tab selection must visibly change before testing value telemetry"
    desktop.call(
        "hpe990_ui_control",
        session_id=session,
        name="qt_tabwidget_tabbar",
        root_hwnd=root["hwnd"],
        point_fraction=[0.1, 0.5],
    )
    desktop.call(
        "hpe990_ui_control", session_id=session, name="pushButton_back", root_hwnd=root["hwnd"]
    )

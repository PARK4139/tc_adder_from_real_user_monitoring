"""Keep UI observation health and real-user measurement claims independent."""

import asyncio
import json
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.functions import observability
from cores.hpe990.functions.operations import OPERATION_TO_TOOL


def test_boundary_without_session_does_not_touch_workers(monkeypatch):
    def forbidden(*args):
        pytest.fail("Boundary-only query must not access a worker")

    monkeypatch.setattr(observability, "ram_status", forbidden)
    monkeypatch.setattr(observability, "semantic_status", forbidden)
    result = observability.automation_observability_status()
    assert result["ui_observation"]["status"] == "NOT_QUERIED"
    assert result["ui_automation"]["interaction_origin"] == "automation"
    assert result["rum"]["status"] == "NOT_IMPLEMENTED"
    assert result["rum"]["metrics"] is None


@pytest.mark.parametrize("active", [False, True])
def test_observer_health_never_implies_rum_instrumentation(monkeypatch, active):
    monkeypatch.setattr(observability, "ram_status", lambda sid: {"active": active})
    monkeypatch.setattr(observability, "semantic_status", lambda sid: {"sampling_healthy": active})
    result = observability.automation_observability_status("owned-session")
    assert result["ui_observation"]["native"]["active"] == active
    assert result["ui_observation"]["semantic"]["sampling_healthy"] == active
    assert result["rum"]["status"] == "NOT_IMPLEMENTED"
    assert result["rum"]["metrics"] is None
    assert not result["rum"]["may_inject_input"]
    assert result["ui_automation"]["whole_application_coverage"] == "UNVERIFIED"


def test_boundary_and_rum_tools_through_mcp():
    async def check():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "cores.hpe990.mcp.server"], cwd=str(D_ROOT)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                discovered = await client.list_tools()
                assert {tool.name for tool in discovered.tools} == set(OPERATION_TO_TOOL.values())
                results = {}
                for name in ("hpe990_automation_observability_status", "hpe990_rum_status"):
                    response = await client.call_tool(name, {})
                    assert not response.isError
                    results[name] = response.structuredContent or json.loads(
                        response.content[0].text
                    )
                boundary = results["hpe990_automation_observability_status"]
                assert boundary["name"] == "UI Automation & Observability"
                assert boundary["rum"] == results["hpe990_rum_status"]
                assert boundary["rum"]["status"] == "NOT_IMPLEMENTED"
                assert boundary["execution_status"] == "NOT_RUN"

    asyncio.run(check())

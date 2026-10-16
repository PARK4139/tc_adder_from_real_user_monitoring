"""Product BDD discovery through the public MCP adapter, without desktop input."""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.functions import scenarios
from cores.hpe990.functions.operations import OPERATION_TO_TOOL
from cores.hpe990.tests.test_tc_review import draft


def test_product_list_keeps_review_state_separate_from_execution(monkeypatch):
    workflow = {"test": "workflow", "tags": ["@product-hpe990"]}
    tool_test = {"test": "ram", "tags": []}
    monkeypatch.setattr(
        scenarios,
        "bdd_registry",
        lambda family: {"family": family, "scenarios": [workflow, tool_test]},
    )
    for state in ("to_review", "reviewed"):
        source = draft("TC-010").replace("@TC-010", f"@TC-010 @review-{state}")
        monkeypatch.setattr(scenarios, "load_review_source", lambda: source)
        result = scenarios.product_bdd_list()
        assert [item["id"] for item in result["scenarios"]] == ["workflow", "TC-010"]
        assert result["scenarios"][1]["review_state"] == state
        assert result["scenarios"][1]["automation_status"] == "unbound"
        assert result["bound_count"] == result["unbound_count"] == 1
        assert result["execution_status"] == "NOT_RUN"


def test_product_list_public_mcp_discovery_and_call():
    async def check():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "cores.hpe990.mcp.server"],
            cwd=str(D_ROOT),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                discovery = await client.list_tools()
                assert {tool.name for tool in discovery.tools} == set(OPERATION_TO_TOOL.values())
                response = await client.call_tool("hpe990_bdd_list", {})
                assert not response.isError
                result = response.structuredContent or json.loads(response.content[0].text)
                assert result["family"] == "hpe990"
                assert result["execution_status"] == "NOT_RUN"
                assert result["total"] == result["bound_count"] + result["unbound_count"]
                workflows = [s for s in result["scenarios"] if s["kind"] == "workflow"]
                assert "test_launch_to_stop_workflow" in {s["id"] for s in workflows}
                assert all("@product-hpe990" in s["tags"] for s in workflows)
                assert result["unbound_count"] > 0
                previous = await client.call_tool("hpe990_bdd_catalog", {})
                assert not previous.isError
                catalog = previous.structuredContent or json.loads(previous.content[0].text)
                assert catalog["family"] == "auto_emulator"
                assert catalog["expected_tests"] == 8

    asyncio.run(check())

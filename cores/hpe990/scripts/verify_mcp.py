"""Exercise discovery and real lifecycle calls through a stdio MCP connection."""

import argparse
import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT, D_TEMP
from cores.hpe990.functions.operations import OPERATION_TO_TOOL


async def verify(command: str, args: list[str], evidence: Path, live: bool = True) -> dict:
    evidence.mkdir(parents=True, exist_ok=True)
    report = {"command": command, "args": args, "checks": [], "calls": {}}
    parameters = StdioServerParameters(command=command, args=args, cwd=str(D_ROOT))
    try:
        with (evidence / "mcp-stderr.log").open("w", encoding="utf-8") as errors:
            async with stdio_client(parameters, errlog=errors) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    tools = await client.list_tools()
                    report["tools"] = [tool.model_dump(mode="json") for tool in tools.tools]
                    names = {tool.name for tool in tools.tools}
                    assert names == set(OPERATION_TO_TOOL.values()), names
                    report["checks"].append("tool_discovery")

                    async def call(name, arguments=None):
                        result = await client.call_tool(name, arguments or {})
                        assert not result.isError, result
                        data = result.structuredContent
                        if data is None:
                            data = json.loads(result.content[0].text)
                        report["calls"].setdefault(name, []).append(data)
                        report.setdefault("invocations", []).append(
                            {
                                "tool": name,
                                "arguments": arguments or {},
                                "result": result.model_dump(mode="json"),
                            }
                        )
                        return data

                    before = await call("hpe990_status")
                    if live:
                        launched = await call("hpe990_launch", {"timeout_seconds": 30})
                        assert launched["ready"] and launched["windows"] and launched["processes"]
                        assert launched["startup_completed"]
                        if not before["running"]:
                            assert (
                                launched["continue_action"]["control_name"] == "pushButton_continue"
                            )
                            assert any(window["title"] == "Edger" for window in launched["windows"])
                        report["checks"].append("continue_to_start")
                        again = await call("hpe990_launch", {"timeout_seconds": 5})
                        assert again["reused"] and again["session_id"] == launched["session_id"]
                        assert {p["pid"] for p in again["processes"]} == {
                            p["pid"] for p in launched["processes"]
                        }
                        report["checks"].extend(
                            ["visible_window", "process_identity", "idempotent_launch"]
                        )
                        monitor = await call(
                            "hpe990_ram_start", {"session_id": launched["session_id"]}
                        )
                        assert monitor["active"]
                        report["checks"].append("ram_active")
                        (evidence / "launch-manifest.json").write_text(
                            json.dumps(launched, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                        if launched["owned"] and not before["running"]:
                            closed = await call(
                                "hpe990_close", {"session_id": launched["session_id"]}
                            )
                            if closed["closed"]:
                                assert not closed["windows"] and not closed["processes"]
                                report["checks"].append("normal_exit")
                            else:
                                report["normal_exit"] = (
                                    "NOT_SUPPORTED: Edger ignores WM_CLOSE; session preserved"
                                )
                        else:
                            report["normal_exit"] = "NOT_TESTED: pre-existing session preserved"
                        catalog = await call(
                            "hpe990_ui_catalog", {"session_id": launched["session_id"]}
                        )
                        assert catalog["observations"]
                        viewer = await call(
                            "hpe990_ui_visualize",
                            {"session_id": launched["session_id"], "open_browser": False},
                        )
                        assert viewer["summary"]["scenarios"] > 0
                        await call("hpe990_ui_viewer_stop")
                        scenario_registry = await call("hpe990_bdd_catalog")
                        assert scenario_registry["expected_tests"] > 0
                        bdd = await call("hpe990_bdd_run", {"allow_desktop_input": True})
                        assert bdd["verdict"] == "PASS" and bdd["concurrent"]["verdict"] == "PASS"
                        verified = set(report["calls"]) | set(
                            bdd["concurrent"]["successful_public_tools"]
                        )
                        missing = names - verified
                        report["function_coverage"] = {
                            "expected_tools": sorted(names),
                            "verified_tools": sorted(verified),
                            "missing": sorted(missing),
                            "coverage_percent": 100 if not missing else 0,
                        }
                        assert not missing, missing
                        report["checks"].extend(
                            ["embedded_bdd_execution", "full_public_tool_call_coverage"]
                        )
                    report["verdict"] = "PASS"
    except BaseException as error:
        report["verdict"] = "FAIL"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (evidence / "mcp-contract-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uv", required=True)
    parser.add_argument("--executable", type=Path)
    parser.add_argument(
        "--evidence", type=Path, default=D_TEMP / "hpe990" / "evidence" / "c35e84d2"
    )
    parser.add_argument("--discovery-only", action="store_true")
    args = parser.parse_args()
    command = str(args.executable) if args.executable else args.uv
    server_args = (
        ["--mcp"]
        if args.executable
        else ["run", "--no-sync", "python", "cores/hpe990/mcp/server.py"]
    )
    result = asyncio.run(verify(command, server_args, args.evidence, not args.discovery_only))
    print(json.dumps({"verdict": result["verdict"], "checks": result["checks"]}))


if __name__ == "__main__":
    main()

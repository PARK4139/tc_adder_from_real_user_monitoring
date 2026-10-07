"""Evidence-backed, read-oriented installed-Emulator exploration via public MCP only."""

import asyncio
import json
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import hpe990_folders


async def explore():
    directory = hpe990_folders.D_HPE990_EVIDENCE / "50c688e3" / str(time.time_ns())
    directory.mkdir(parents=True)
    report = {"calls": [], "paths": [], "unexplored": []}
    parameters = StdioServerParameters(
        command=str(D_ROOT / ".venv/Scripts/python.exe"),
        args=["-m", "cores.hpe990.mcp.server"],
        cwd=str(D_ROOT),
    )
    with (directory / "mcp-stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(parameters, errlog=errors) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                report["tools"] = [
                    t.model_dump(mode="json") for t in (await client.list_tools()).tools
                ]

                async def call(tool, **arguments):
                    result = await client.call_tool(tool, arguments)
                    report["calls"].append(
                        {
                            "name": tool,
                            "arguments": arguments,
                            "result": result.model_dump(mode="json"),
                        }
                    )
                    if result.isError:
                        raise RuntimeError(result.content)
                    return result.structuredContent or json.loads(result.content[0].text)

                status = await call("hpe990_launch")
                session_id = status["session_id"]
                report["session_id"] = session_id
                await call("hpe990_ram_start", session_id=session_id)

                async def snapshot():
                    return await call("hpe990_ui_collect", session_id=session_id)

                async def click(name, root=None, action="click", hwnd=None):
                    return await call(
                        "hpe990_ui_control",
                        session_id=session_id,
                        name=name,
                        root_hwnd=root,
                        action=action,
                        hwnd=hwnd,
                    )

                async def active_root():
                    observed = await snapshot()
                    candidates = [
                        r
                        for r in observed["roots"]
                        if r["visible"] and r["enabled"] and r["class_name"] == "QWidget"
                    ]
                    return observed, candidates

                # Settings pages can be inspected without applying configuration or running tests.
                await click("pushButton_setting")
                setup, roots = await active_root()
                setup_root = next(r for r in roots if r["name"] == "Setup")
                pages = [
                    "pushButton_preferences",
                    "pushButton_statistics",
                    "pushButton_date_time",
                    "pushButton_config_backup_restore",
                    "pushButton_edger_adjustments",
                    "pushButton_edger_calibration",
                    "pushButton_edger_wheel_dressing",
                    "pushButton_edger_test_mode",
                    "pushButton_maintenance",
                ]
                for page in pages:
                    try:
                        await click(page, setup_root["hwnd"])
                        observed, roots = await active_root()
                        report["paths"].append(
                            {"control": page, "roots": roots, "evidence": observed["evidence"]}
                        )
                        others = [r for r in roots if r["hwnd"] != setup_root["hwnd"]]
                        if others:
                            active = others[0]
                            descendants = {active["hwnd"]}
                            for _ in range(len(observed["nodes"])):
                                descendants.update(
                                    n["hwnd"]
                                    for n in observed["nodes"]
                                    if n["parent"] in descendants
                                )
                            back = [
                                n
                                for n in observed["nodes"]
                                if n["hwnd"] in descendants
                                and n["visible"]
                                and n["enabled"]
                                and n["name"]
                                in ("pushButton_back", "pushButton_cancel", "pushButton_close")
                            ]
                            if len(back) == 1:
                                await click(back[0]["name"], active["hwnd"])
                            else:
                                await click(active["name"], active["hwnd"], "escape")
                            _, restored = await active_root()
                            if not any(r["name"] == "Setup" for r in restored):
                                report["unexplored"].append(
                                    {"page": page, "reason": "Escape/back did not restore Setup"}
                                )
                                break
                    except Exception as error:
                        report["unexplored"].append({"page": page, "reason": str(error)})
                        break
                report["catalog"] = await call("hpe990_ui_catalog", session_id=session_id)
                report["unexplored"].extend(
                    [
                        {
                            "page": "software upgrade",
                            "reason": "Requires designated upgrade fixture and rollback boundary",
                        },
                        {
                            "page": "job-dependent editing/grinding",
                            "reason": "No validated disposable lens/job corpus supplied",
                        },
                        {
                            "page": "Shutdown Yes",
                            "reason": "Observed prompt requests system shutdown, not application-only exit",
                        },
                    ]
                )
                report["whole_application_complete"] = False
                report["evidence"] = str(directory / "mcp-contract-report.json")
                (directory / "mcp-contract-report.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(
                    json.dumps(
                        {
                            "session_id": session_id,
                            "evidence": report["evidence"],
                            "paths": len(report["paths"]),
                            "unexplored": report["unexplored"],
                        }
                    )
                )


if __name__ == "__main__":
    asyncio.run(explore())

"""Traverse observed Setup pages through public MCP and retain every protocol receipt."""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import hpe990_folders

PAGES = (
    ("pushButton_preferences", "Preferences"),
    ("pushButton_statistics", "Statistics"),
    ("pushButton_date_time", "Date/Time"),
    ("pushButton_config_backup_restore", "Configuration Management"),
    ("pushButton_touch_test", "Touchscreen Check"),
    ("pushButton_edger_adjustments", "Adjustments"),
    ("pushButton_edger_test_mode", "Test Mode"),
    ("pushButton_edger_wheel_dressing", "Wheel Dressing"),
    ("pushButton_edger_calibration", "Calibration"),
    ("pushButton_software_upgrade", "Software Upgrade"),
    ("pushButton_maintenance", "Maintenance"),
)


async def collect_routes(directory: Path, accessibility_backend: str = "msaa"):
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "routes.json").exists():
        raise FileExistsError("Use a new evidence directory; previous receipts must be preserved")
    report = {"routes": [], "unresolved": [], "inventories": []}
    counter = 0

    def save():
        (directory / "routes.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "cores.hpe990.mcp.server"], cwd=str(D_ROOT)
    )
    with (directory / "route-mcp.stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()

                async def call(tool, **arguments):
                    nonlocal counter
                    counter += 1
                    response = await client.call_tool(tool, arguments)
                    (directory / f"route-{counter:04d}-{tool}.json").write_text(
                        response.model_dump_json(), encoding="utf-8"
                    )
                    if response.isError:
                        raise RuntimeError(str(response.content))
                    data = response.structuredContent or json.loads(response.content[0].text)
                    for key in ("before", "after", "evidence"):
                        path = data.get(key)
                        if isinstance(path, str) and Path(path).name == "inventory.json":
                            if tool in ("hpe990_ui_keys", "hpe990_ui_activate"):
                                continue
                            report["inventories"].append(path)
                    save()
                    return data

                status = await call("hpe990_status")
                if not status["running"]:
                    status = await call("hpe990_launch")
                sid = report["session_id"] = status["session_id"]
                await call("hpe990_ram_start", session_id=sid)
                await call("hpe990_ram_semantic_start", session_id=sid)

                async def snapshot():
                    return await call(
                        "hpe990_ui_collect",
                        session_id=sid,
                        refresh_templates=False,
                        accessibility_backend=accessibility_backend,
                    )

                async def click(node, root):
                    return await call(
                        "hpe990_ui_control",
                        session_id=sid,
                        name=node["name"],
                        hwnd=node["hwnd"],
                        root_hwnd=root["hwnd"],
                        refresh_templates=False,
                    )

                def roots(record):
                    return [r for r in record["roots"] if r["visible"] and r["enabled"]]

                def descendants(record, root):
                    handles = {root["hwnd"]}
                    for _ in record["nodes"]:
                        extra = {n["hwnd"] for n in record["nodes"] if n["parent"] in handles}
                        if extra <= handles:
                            break
                        handles |= extra
                    return [
                        n
                        for n in record["nodes"]
                        if n["hwnd"] in handles and n["visible"] and n["enabled"]
                    ]

                async def close_page(record, root):
                    nodes = descendants(record, root)
                    for name in ("pushButton_cancel", "pushButton_close", "pushButton_back"):
                        candidates = [n for n in nodes if n["name"] == name]
                        if len(candidates) == 1:
                            await click(candidates[0], root)
                            await asyncio.sleep(0.5)
                            return await snapshot()
                    for label in ("Cancel", "Close", "Back"):
                        visual = [
                            e
                            for e in record.get("visual", {}).get("elements", [])
                            if e.get("root_hwnd") == root["hwnd"] and e.get("name") == label
                        ]
                        if len(visual) == 1:
                            left, top, right, bottom = visual[0]["rect"]
                            x = root["rect"][0] + (left + right) / 2
                            y = root["rect"][1] + (top + bottom) / 2
                            native = [
                                n
                                for n in nodes
                                if n["hwnd"] != root["hwnd"]
                                and n["rect"][0] < x < n["rect"][2]
                                and n["rect"][1] < y < n["rect"][3]
                            ]
                            native.sort(
                                key=lambda n: (
                                    (n["rect"][2] - n["rect"][0]) * (n["rect"][3] - n["rect"][1])
                                )
                            )
                            if native:
                                await click(native[0], root)
                                await asyncio.sleep(0.5)
                                return await snapshot()
                            await call("hpe990_ui_activate", session_id=sid, ui_id=root["ui_id"])
                            await call(
                                "hpe990_ui_control_visual",
                                session_id=sid,
                                ui_id=visual[0]["ui_id"],
                                refresh_templates=False,
                            )
                            await asyncio.sleep(0.5)
                            return await snapshot()
                    raise RuntimeError(f"No observed cancel/close/back control for {root['name']}")

                record = await snapshot()
                current = [
                    r
                    for r in roots(record)
                    if r["name"] not in ("Notification", "Setup", "Edger", "Start")
                ]
                if current:
                    record = await close_page(record, current[0])
                if not any(r["name"] == "Setup" for r in roots(record)):
                    edger = next(r for r in roots(record) if r["name"] == "Edger")
                    node = next(
                        n for n in descendants(record, edger) if n["name"] == "pushButton_setting"
                    )
                    await click(node, edger)
                    await asyncio.sleep(0.5)
                    record = await snapshot()

                for button, expected in PAGES:
                    print(f"Collecting Setup > {expected}", flush=True)
                    try:
                        setup = next(r for r in roots(record) if r["name"] == "Setup")
                        candidates = [n for n in descendants(record, setup) if n["name"] == button]
                        if len(candidates) != 1:
                            raise RuntimeError("Navigation control missing or ambiguous")
                        receipt = await click(candidates[0], setup)
                        assert receipt["ram_active"]
                        await asyncio.sleep(0.5)
                        record = await snapshot()
                        active = [
                            r
                            for r in roots(record)
                            if r["name"] not in ("Notification", "Setup", "Edger", "Start")
                        ]
                        if len(active) != 1:
                            report["unresolved"].append(
                                {
                                    "route": expected,
                                    "reason": "No unique destination screen appeared",
                                }
                            )
                            save()
                            continue
                        root = active[0]
                        route = {
                            "requested": expected,
                            "actual": root["name"],
                            "button": button,
                            "action_id": receipt["action_id"],
                            "snapshots": [record["evidence"]],
                            "pages": [],
                        }
                        report["routes"].append(route)
                        seen = set()
                        for _ in range(16):
                            nodes = descendants(record, root)
                            pages = tuple(
                                n["name"] for n in nodes if n["name"].startswith(("tab_", "page_"))
                            )
                            route["pages"].append(list(pages))
                            bars = [n for n in nodes if n["name"] == "qt_tabwidget_tabbar"]
                            if not bars or pages in seen:
                                break
                            seen.add(pages)
                            await call(
                                "hpe990_ui_keys",
                                session_id=sid,
                                ui_id=bars[0]["ui_id"],
                                keys=["Right"],
                            )
                            await asyncio.sleep(0.5)
                            record = await snapshot()
                            route["snapshots"].append(record["evidence"])
                            save()
                        record = await close_page(record, root)
                        route["returned_to_setup"] = any(
                            r["name"] == "Setup" for r in roots(record)
                        )
                        save()
                        if not route["returned_to_setup"]:
                            raise RuntimeError("Return to Setup not observed")
                    except Exception as error:
                        report["unresolved"].append({"route": expected, "reason": str(error)})
                        save()
                        break
                report["native_status"] = await call("hpe990_ram_status", session_id=sid)
                report["semantic_status"] = await call("hpe990_ram_semantic_status", session_id=sid)
                report["audit"] = await call(
                    "hpe990_ui_collection_audit",
                    session_id=sid,
                    inventory_paths=report["inventories"],
                )
                report["whole_application_complete"] = False
                save()
                print(
                    json.dumps(
                        {
                            "evidence": str(directory),
                            "routes": len(report["routes"]),
                            "unresolved": report["unresolved"],
                            "audit": report["audit"]["evidence_verdict"],
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-directory", type=Path)
    parser.add_argument("--accessibility-backend", choices=("msaa", "uia", "none"), default="msaa")
    args = parser.parse_args()
    destination = args.evidence_directory or hpe990_folders.D_HPE990_EVIDENCE / "50c688e3" / str(
        time.time_ns()
    )
    if not destination.resolve().is_relative_to(hpe990_folders.D_HPE990_EVIDENCE.resolve()):
        parser.error("Use the external family evidence directory")
    asyncio.run(collect_routes(destination, args.accessibility_backend))

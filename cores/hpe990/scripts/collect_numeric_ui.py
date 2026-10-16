"""Collect observed input modals through MCP without typing replacement values."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import hpe990_folders


async def run(directory: Path, parent_name: str, fields: list[str]):
    directory.mkdir(parents=True)
    report = {"routes": [], "unresolved": []}
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "cores.hpe990.mcp.server"], cwd=str(D_ROOT)
    )
    with (directory / "mcp.stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                counter = 0

                async def call(tool, **arguments):
                    nonlocal counter
                    counter += 1
                    result = await client.call_tool(tool, arguments)
                    (directory / f"{counter:03d}-{tool}.json").write_text(
                        result.model_dump_json(), encoding="utf-8"
                    )
                    if result.isError:
                        raise RuntimeError(str(result.content))
                    return result.structuredContent or json.loads(result.content[0].text)

                sid = (await call("hpe990_status"))["session_id"]
                report["session_id"] = sid

                async def snapshot():
                    return await call("hpe990_ui_collect", session_id=sid, refresh_templates=False)

                def nodes(record, root):
                    handles = {root["hwnd"]}
                    for _ in record["nodes"]:
                        added = {n["hwnd"] for n in record["nodes"] if n["parent"] in handles}
                        if added <= handles:
                            break
                        handles |= added
                    return [
                        n
                        for n in record["nodes"]
                        if n["hwnd"] in handles and n["visible"] and n["enabled"]
                    ]

                async def click(node, root):
                    result = await call(
                        "hpe990_ui_control",
                        session_id=sid,
                        name=node["name"],
                        hwnd=node["hwnd"],
                        root_hwnd=root["hwnd"],
                        refresh_templates=False,
                    )
                    assert result["ram_active"]
                    return result

                def parent(record):
                    return next(
                        n
                        for n in record["roots"]
                        if n["name"] == parent_name and n["visible"] and n["enabled"]
                    )

                record = await snapshot()
                active = [
                    r
                    for r in record["roots"]
                    if r["visible"]
                    and r["enabled"]
                    and r["name"] not in ("Notification", parent_name, "Edger", "Start")
                ]
                if active:
                    root = active[0]
                    button = next(n for n in nodes(record, root) if n["name"] == "pushButton_enter")
                    await click(button, root)
                    record = await snapshot()
                for field in fields:
                    print(f"Collecting {parent_name} > {field}", flush=True)
                    try:
                        root = parent(record)
                        name, separator, handle = field.partition("@")
                        candidates = [
                            n
                            for n in nodes(record, root)
                            if n["name"] == name and (not separator or n["hwnd"] == int(handle))
                        ]
                        if len(candidates) != 1:
                            raise ValueError("Field is missing or ambiguous")
                        request = await click(candidates[0], root)
                        record = await snapshot()
                        active = [
                            r
                            for r in record["roots"]
                            if r["visible"]
                            and r["enabled"]
                            and r["name"] not in ("Notification", parent_name, "Edger", "Start")
                        ]
                        if len(active) != 1:
                            report["unresolved"].append(
                                {"field": field, "reason": "No unique input modal appeared"}
                            )
                            continue
                        modal = active[0]
                        route = {
                            "actual": modal["name"],
                            "requested": modal["name"],
                            "parent": parent_name,
                            "field": field,
                            "action_id": request["action_id"],
                            "snapshots": [record["evidence"]],
                            "return_label": "↵",
                            "replacement_values_entered": False,
                        }
                        report["routes"].append(route)
                        enter = [n for n in nodes(record, modal) if n["name"] == "pushButton_enter"]
                        if len(enter) != 1:
                            raise ValueError("Input modal lacks a unique observed confirm button")
                        await click(enter[0], modal)
                        record = await snapshot()
                        if not any(
                            r["name"] == parent_name and r["visible"] and r["enabled"]
                            for r in record["roots"]
                        ):
                            raise RuntimeError(
                                f"Confirm did not restore {parent_name}; active roots: {[r['name'] for r in record['roots'] if r['visible'] and r['enabled']]}"
                            )
                        parent(record)
                        route["returned_to_parent"] = True
                    except Exception as error:
                        report["unresolved"].append({"field": field, "reason": str(error)})
                        break
                    finally:
                        (directory / "routes.json").write_text(
                            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                print(
                    json.dumps(
                        {"routes": len(report["routes"]), "unresolved": report["unresolved"]}
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-directory", type=Path, required=True)
    parser.add_argument("--parent", default="Job Editor")
    parser.add_argument("fields", nargs="+")
    args = parser.parse_args()
    if not args.evidence_directory.resolve().is_relative_to(
        hpe990_folders.D_HPE990_EVIDENCE.resolve()
    ):
        parser.error("Use external family evidence")
    asyncio.run(run(args.evidence_directory, args.parent, args.fields))

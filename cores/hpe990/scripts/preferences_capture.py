"""Record public MCP observations/actions for Preferences review authoring."""

import argparse
import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import hpe990_folders


def payload(record):
    result = record.get("result", record)
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def summarize(data):
    if data.get("after"):
        data = json.loads(Path(data["after"]).read_text(encoding="utf-8"))
    return {
        "keys": list(data),
        "roots": [
            {k: n.get(k) for k in ("name", "ui_id", "hwnd", "rect", "enabled")}
            for n in data.get("roots", [])
            if n.get("visible")
        ],
        "pages": [
            {k: n.get(k) for k in ("name", "ui_id", "hwnd", "rect")}
            for n in data.get("nodes", [])
            if n.get("visible")
            and (n.get("name", "").startswith("tab_") or n.get("name") == "qt_tabwidget_tabbar")
        ],
        "screenshots": data.get("screenshots"),
        "visual": [
            {k: n.get(k) for k in ("name", "ui_id", "root_hwnd", "rect", "control_type")}
            for n in data.get("visual", {}).get("elements", [])
        ],
        "evidence": data.get("evidence"),
    }


async def run(requests, directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "mcp.stderr.log").open("a", encoding="utf-8") as errors:
        async with stdio_client(
            StdioServerParameters(
                command=str(D_ROOT / ".venv/Scripts/python.exe"),
                args=["-m", "cores.hpe990.mcp.server"],
                cwd=str(D_ROOT),
            ),
            errlog=errors,
        ) as (r, w):
            async with ClientSession(r, w) as client:
                await client.initialize()
                for request in requests:
                    path = directory / (request["label"] + ".json")
                    if path.exists():
                        raise ValueError(f"Refuse to replace protocol evidence: {path}")
                    print(f"Calling {request['tool']}: {request['label']}", flush=True)
                    result = await client.call_tool(request["tool"], request.get("arguments", {}))
                    path.write_text(
                        json.dumps(
                            {**request, "result": result.model_dump(mode="json")},
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    if result.isError:
                        raise RuntimeError(f"MCP failed; retained {path}")
                    data = payload(result.model_dump(mode="json"))
                    compact = summarize(data)
                    path.with_suffix(".summary.json").write_text(
                        json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    print(
                        json.dumps(
                            {
                                "saved": str(path),
                                "roots": compact["roots"],
                                "pages": compact["pages"],
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path)
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--evidence-directory", type=Path)
    args = parser.parse_args()
    if args.inspect:
        print(
            json.dumps(
                summarize(payload(json.loads(args.inspect.read_text(encoding="utf-8")))),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if args.requests is None or args.evidence_directory is None:
            parser.error("--requests and --evidence-directory are required for MCP calls")
        destination = args.evidence_directory.resolve()
        if not destination.is_relative_to(hpe990_folders.D_HPE990_EVIDENCE.resolve()):
            parser.error("Evidence directory must be inside the external family evidence root")
        asyncio.run(
            run(
                json.loads(args.requests.read_text(encoding="utf-8-sig")),
                destination,
            )
        )

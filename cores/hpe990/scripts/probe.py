"""Read or invoke one public MCP tool and retain its actual protocol evidence."""

import argparse
import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import hpe990_folders


async def probe(tool: str, arguments: dict, output: str, executable: str | None = None):
    path = hpe990_folders.D_HPE990_EVIDENCE / "inspection" / output
    path.parent.mkdir(parents=True, exist_ok=True)
    command = executable or str(D_ROOT / ".venv" / "Scripts" / "python.exe")
    args = ["--mcp"] if executable else ["-m", "cores.hpe990.mcp.server"]
    with path.with_suffix(".stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(
            StdioServerParameters(command=command, args=args, cwd=str(D_ROOT)), errlog=errors
        ) as (r, w):
            async with ClientSession(r, w) as client:
                await client.initialize()
                discovered = await client.list_tools()
                result = await client.call_tool(tool, arguments)
                record = {
                    "tools": [t.model_dump(mode="json") for t in discovered.tools],
                    "tool": tool,
                    "arguments": arguments,
                    "result": result.model_dump(mode="json"),
                }
                path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                data = result.structuredContent
                if data is None and not result.isError:
                    data = json.loads(result.content[0].text)
                print(
                    json.dumps(
                        {
                            "tool": tool,
                            "isError": result.isError,
                            "evidence": str(path),
                            "summary": {
                                k: v
                                for k, v in (data or {}).items()
                                if k not in ("snapshot", "events", "windows", "nodes", "roots")
                            },
                        },
                        ensure_ascii=False,
                    )
                )
                if result.isError:
                    raise RuntimeError(f"MCP error; evidence={path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tool")
    parser.add_argument("--arguments", type=Path)
    parser.add_argument("--output", default="probe.json")
    parser.add_argument("--executable")
    args = parser.parse_args()
    arguments = json.loads(args.arguments.read_text(encoding="utf-8-sig")) if args.arguments else {}
    asyncio.run(probe(args.tool, arguments, args.output, args.executable))

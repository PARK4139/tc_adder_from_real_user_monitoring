"""Executable entry: launch by default; use --mcp for stdio MCP service."""

import argparse
import json
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cores.hpe990.common.version import DEPLOYMENT_VERSION
from cores.hpe990.mcp.tools.lifecycle import hpe990_close, hpe990_launch, hpe990_status


def main() -> int:
    parser = argparse.ArgumentParser(description="HPE990 Emulator launcher / MCP service")
    parser.add_argument(
        "--version", action="version", version=f"auto_emulator {DEPLOYMENT_VERSION}"
    )
    parser.add_argument("--mcp", action="store_true", help="serve MCP over stdio")
    parser.add_argument("--backend", help=argparse.SUPPRESS)
    parser.add_argument("--bdd-worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "action", nargs="?", choices=["launch", "status", "close"], default="launch"
    )
    parser.add_argument("--session-id")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    try:
        if args.bdd_worker:
            from cores.common.functions.run_family_bdd import frozen_bdd_worker

            return frozen_bdd_worker(args.bdd_worker)
        if args.backend:
            from cores.hpe990.functions.backend import run_backend

            run_backend(args.backend)
            return 0
        if args.mcp:
            from cores.hpe990.mcp.server import mcp

            mcp.run(transport="stdio")
            return 0
        if args.action == "close":
            if not args.session_id:
                parser.error("close requires --session-id")
            result = hpe990_close(args.session_id, args.timeout)
        elif args.action == "status":
            result = hpe990_status()
        else:
            result = hpe990_launch(args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("closed", result.get("ready", True)) else 1
    except Exception as error:
        print(
            json.dumps({"error": type(error).__name__, "message": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

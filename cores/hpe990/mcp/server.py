"""Client-owned HPE990 MCP stdio adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp.server.fastmcp import FastMCP

from cores.hpe990.functions.lifecycle import log_event
from cores.hpe990.mcp.tools.analysis import hpe990_ui_analyze
from cores.hpe990.mcp.tools.lifecycle import hpe990_close, hpe990_launch, hpe990_status, hpe990_stop
from cores.hpe990.mcp.tools.monitoring import (
    hpe990_ram_start,
    hpe990_ram_status,
    hpe990_ram_stop,
    hpe990_telemetry_export,
    hpe990_telemetry_read,
)
from cores.hpe990.mcp.tools.scenarios import hpe990_bdd_catalog, hpe990_bdd_run
from cores.hpe990.mcp.tools.ui import (
    hpe990_ui_catalog,
    hpe990_ui_collect,
    hpe990_ui_control,
    hpe990_ui_viewer_stop,
    hpe990_ui_visualize,
    hpe990_window_geometry,
)

mcp = FastMCP("pk-hpe990-mcp")
for tool in (
    hpe990_launch,
    hpe990_status,
    hpe990_close,
    hpe990_stop,
    hpe990_ram_start,
    hpe990_ram_status,
    hpe990_ram_stop,
    hpe990_telemetry_read,
    hpe990_ui_collect,
    hpe990_ui_control,
    hpe990_ui_catalog,
    hpe990_window_geometry,
    hpe990_ui_visualize,
    hpe990_ui_viewer_stop,
    hpe990_telemetry_export,
    hpe990_ui_analyze,
    hpe990_bdd_catalog,
    hpe990_bdd_run,
):
    mcp.tool()(tool)

if __name__ == "__main__":
    log_event("adapter_started")
    try:
        mcp.run(transport="stdio")
    finally:
        # Ending a client connection must not terminate the Emulator session.
        log_event("adapter_stopped")

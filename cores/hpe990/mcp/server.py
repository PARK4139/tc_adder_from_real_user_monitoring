"""Client-owned HPE990 MCP stdio adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp.server.fastmcp import FastMCP

from cores.hpe990.functions.lifecycle import log_event
from cores.hpe990.mcp.tools.analysis import hpe990_ui_analyze
from cores.hpe990.mcp.tools.identity import hpe990_ui_registry_backup
from cores.hpe990.mcp.tools.lifecycle import hpe990_close, hpe990_launch, hpe990_status, hpe990_stop
from cores.hpe990.mcp.tools.mapping import (
    hpe990_ui_control_semantic,
    hpe990_ui_map,
    hpe990_ui_resolve,
)
from cores.hpe990.mcp.tools.monitoring import (
    hpe990_ram_semantic_read,
    hpe990_ram_semantic_start,
    hpe990_ram_semantic_status,
    hpe990_ram_semantic_stop,
    hpe990_ram_start,
    hpe990_ram_status,
    hpe990_ram_stop,
    hpe990_telemetry_export,
    hpe990_telemetry_read,
)
from cores.hpe990.mcp.tools.observability import (
    hpe990_automation_observability_status,
    hpe990_rum_status,
)
from cores.hpe990.mcp.tools.scenarios import (
    hpe990_bdd_catalog,
    hpe990_bdd_list,
    hpe990_bdd_run,
    hpe990_tc_templates,
)
from cores.hpe990.mcp.tools.server_manager import mcp_server_manager
from cores.hpe990.mcp.tools.ui import (
    hpe990_ui_activate,
    hpe990_ui_catalog,
    hpe990_ui_collect,
    hpe990_ui_collection_audit,
    hpe990_ui_control,
    hpe990_ui_control_visual,
    hpe990_ui_drag,
    hpe990_ui_input_inventory,
    hpe990_ui_keys,
    hpe990_ui_viewer_stop,
    hpe990_ui_visualize,
    hpe990_window_geometry,
    hpe990_window_minimize,
)

mcp = FastMCP("auto_emulator MCP", host="127.0.0.1", port=8765)
for tool in (
    mcp_server_manager,
    hpe990_automation_observability_status,
    hpe990_rum_status,
    hpe990_ui_registry_backup,
    hpe990_ui_map,
    hpe990_ui_resolve,
    hpe990_ui_control_semantic,
    hpe990_ram_semantic_start,
    hpe990_ram_semantic_status,
    hpe990_ram_semantic_stop,
    hpe990_ram_semantic_read,
    hpe990_launch,
    hpe990_status,
    hpe990_close,
    hpe990_stop,
    hpe990_ram_start,
    hpe990_ram_status,
    hpe990_ram_stop,
    hpe990_telemetry_read,
    hpe990_ui_collect,
    hpe990_ui_collection_audit,
    hpe990_ui_control,
    hpe990_ui_drag,
    hpe990_ui_keys,
    hpe990_ui_activate,
    hpe990_ui_input_inventory,
    hpe990_ui_control_visual,
    hpe990_ui_catalog,
    hpe990_window_geometry,
    hpe990_window_minimize,
    hpe990_ui_visualize,
    hpe990_ui_viewer_stop,
    hpe990_telemetry_export,
    hpe990_ui_analyze,
    hpe990_bdd_catalog,
    hpe990_bdd_list,
    hpe990_bdd_run,
    hpe990_tc_templates,
):
    mcp.tool()(tool)

if __name__ == "__main__":
    http_mode = "--mcp-http" in sys.argv
    log_event("adapter_started")
    try:
        mcp.run(transport="streamable-http" if http_mode else "stdio")
    finally:
        # Ending a client connection must not terminate the Emulator session.
        log_event("adapter_stopped")

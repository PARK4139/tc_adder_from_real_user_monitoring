"""Implemented public Emulator operations, independently audited against MCP discovery."""

OPERATION_TO_TOOL = {
    "launch_continue_ready": "hpe990_launch",
    "process_and_window_status": "hpe990_status",
    "normal_close_request": "hpe990_close",
    "explicit_owned_application_stop": "hpe990_stop",
    "start_continuous_ram": "hpe990_ram_start",
    "monitor_status_metrics": "hpe990_ram_status",
    "stop_and_flush_ram": "hpe990_ram_stop",
    "read_sequenced_events": "hpe990_telemetry_read",
    "export_validate_local_events": "hpe990_telemetry_export",
    "native_hierarchy_screenshots": "hpe990_ui_collect",
    "observed_control_input": "hpe990_ui_control",
    "inventory_and_unvisited_frontier": "hpe990_ui_catalog",
    "dynamic_collected_ui_visualization": "hpe990_ui_visualize",
    "stop_local_ui_viewer": "hpe990_ui_viewer_stop",
    "move_resize_session_window": "hpe990_window_geometry",
    "observed_state_transition_analysis": "hpe990_ui_analyze",
    "registered_scenarios_traceability": "hpe990_bdd_catalog",
    "execute_real_bdd_with_ram": "hpe990_bdd_run",
}

"""Canonical requirement for MCP coverage of HPE990 Emulator operations."""

RULE_ID = "HPE990_MCP_FUNCTION_COVERAGE"
TITLE = "Expose every Emulator operation through MCP"
SOURCE = "cores/hpe990/rules/mcp_function_coverage.py"
STATUS = "active"
BODY = """
## Requirement
- Basis: user directive, 2026-10-06: Emulator의 모든기능은 mcp 로 구현해야합니다.
- Every Emulator operation must be available through callable MCP tools,
  including lifecycle, UI interactions, RAM, collection, telemetry, and analysis.
- Derive the complete product-operation inventory from observed UI analysis;
  do not assume the current backlog lists every Emulator function.
- Host the family protocol adapter at cores/hpe990/mcp/server.py with tool
  groups in cores/hpe990/mcp/tools/. Keep the server thin and use family-owned
  Python/Rust implementations. Manage Python dependencies and execution with uv.
- Register the implemented server in project-local .mcp.json using a portable
  uv launcher. Do not register nonexistent implementations.
- BDD automation must invoke the same public MCP tools used by clients.
  RAM must remain active during tool execution and session shutdown.
- Verify discovered tool schemas and actual MCP calls, not only direct function
  calls. Each operation needs a tool mapping and observed expected/actual evidence.
- Completion requires 100% coverage of the verified operation inventory, zero
  unmapped operations, and zero failed required tool-call acceptance checks.
  Unexplored functions remain explicitly unresolved; do not claim full coverage.
- Remote telemetry transmission remains future work; record locally now.
"""

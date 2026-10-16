"""Responsibility boundary for UI Automation & Observability."""

RULE_ID = "HPE990_AUTOMATION_OBSERVABILITY_BOUNDARY"
TITLE = "UI Automation & Observability responsibility boundary"
SOURCE = "cores/hpe990/rules/automation_observability.py"
STATUS = "active"
BODY = """
- Umbrella name: UI Automation & Observability.
- Spell out Real Activity Monitoring in prose, tool descriptions, diagnostics and
  BDD steps. Preserve lowercase ram identifiers in APIs, schemas and evidence paths.
- UI Automation owns UI discovery, identity mapping, navigation, input delivery,
  pre/post snapshots and verification of requested application outcomes.
- UI observation owns passive window, hierarchy, image/text/value change streams,
  worker health, sampling gaps and local evidence retention. Existing Real Activity Monitoring names
  designate these project observers, not industry-standard RUM instrumentation.
- RUM owns attributed real-user sessions, interaction-to-response latency, observed
  application errors and user-experience metrics. It must not navigate or inject input.
- Automated interactions belong to automation evidence/synthetic measurements;
  unknown-origin window events must not be labelled real-user interactions.
- Shared evidence correlates session_id, run_id, sequence, timestamp and action_id
  where available. Temporal proximity alone does not establish causality.
- Report collection completeness, delivery, outcome verification, observer health
  and RUM instrumentation independently. None implies another or a functional PASS.
- Until real-user origin and response/error instrumentation exists, RUM reports
  NOT_IMPLEMENTED and no metrics. Never rename Real Activity Monitoring timing/sample data into RUM.
- Keep existing MCP identifiers and runtime evidence paths stable during this
  responsibility split. Expose read-only boundary and RUM capability status via MCP.
"""

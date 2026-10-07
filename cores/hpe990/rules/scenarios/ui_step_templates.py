"""Canonical contract for UI-ID-bound reusable numbered step templates."""

RULE_ID = "HPE990_UI_STEP_TEMPLATES"
TITLE = "Generate UI element step drafts from reusable type templates"
SOURCE = "cores/hpe990/rules/scenarios/ui_step_templates.py"
STATUS = "active"
BODY = """
- Every collected screen, modal, popup and child control must have a template binding
  keyed by its UI SSOT ui_id. UI identities and TC numeric IDs are distinct.
- Store reusable type template bodies only in configs/ui_step_templates.json;
  store verified per-element type/specification bindings in configs/ui_step_bindings.json.
  Never keep copied per-element template bodies as competing authoring authorities.
- Use numbered No. | Steps | Expected Result groups and individual TC prerequisites.
  Wording follows rules/scenarios/tc_up_dictionary.py; do not duplicate its rules.
- Support window/modal/popup, selectors, inputs/numbers, checkbox/radio, buttons and
  display fields. Offer boundary, save/reopen and cancel/reopen variants separately.
- Unknown types use an explicitly unresolved display/type-confirmation template.
  Naming/provider hints and existing TC declarations are candidates, not verified types.
  Do not infer editability from a rectangle or treat static data as an editable input.
- Resolve only supplied/verified names, paths, values, options, ranges and outcomes.
  Keep missing specifications visible as placeholders and concrete pending labels.
  Even fully specified generated cases remain drafts until independently executed.
- Numeric boundaries include minimum, maximum, below/above and inclusive lower/upper
  cases. Never infer increment, range, rejection, rounding or saving behavior.
- Example: UI-000111 Backup Date -> display template; expected_display_value stays
  pending until specified. A verified Language selector -> click/dropdown/options,
  then select/value steps. A modal gets its own binding, and its OK button another.
- Expose template discovery and generated per-UI groups through public MCP. Generate
  JSON/HTML review artifacts from the same catalog; collection can refresh them.
- Existing authored TC IDs/prerequisites and accepted outcomes must not be overwritten
  by bulk generation. Promote reviewed drafts using existing TC allocation rules.
- PASS for this implementation means every catalogued UI ID has a valid template
  draft with traceable source and pending specifications; it is not UI test coverage PASS.
"""

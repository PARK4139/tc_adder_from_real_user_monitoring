"""Canonical version-scoped semantic UI mapping contract."""

RULE_ID = "HPE990_VERSIONED_UI_MAPPING"
TITLE = "Version-aware internal UI names and semantic ID mappings"
SOURCE = "cores/hpe990/rules/versioned_ui_mapping.py"
STATUS = "active"
BODY = """
- Keep common meaning IDs in configs/ui_semantics.json; never encode HWND, session,
  version, translated labels or TC numeric IDs into those identities.
- Identify a mapping target by product model and executable SHA-256. Preserve PE
  file/product versions and executable path as evidence. Unknown PE versions remain
  unknown; do not replace them with a filename or an unrelated reviewed target version.
- Internal names are GetWindowText observations, not verified Qt objectName or control
  semantics. Preserve observed native names, class, full ancestry, UI ID, session,
  timestamp and source evidence in the existing UI identity SQLite SSOT.
- Native ID coverage does not imply whole-application discovery or meaning coverage.
  Unmapped native elements remain unmapped. OCR/accessibility-only elements retain
  their existing evidence and must not receive fabricated native mappings.
- A semantic definition can declare target-hash-specific selector variants. New
  versions stay candidates until explicitly verified through public MCP with one
  current visible/enabled native candidate and its exact observed UI ID.
- Confirmation proves identity association, not application behavior or specification
  compliance. Retain version, selector, definition, verification time and evidence.
- Before control, resolve against a fresh same-version observation. Reject unknown
  or unconfirmed versions, ambiguity, missing ancestry, changed definitions/selectors,
  hidden/disabled/clipped controls. Recheck the full native path before dispatch.
- Normalize only explicitly reviewed root display aliases. Do not fuzzy-match an
  unrecognized internal name or silently select one of several matching controls.
- Existing UI-xxxxxx IDs and raw evidence are preserved. HWND recreation can map to
  the same meaning when version and verified structure agree; HWND itself is not SSOT.
- Expose map observation/catalog/verification/revocation, resolution and semantic
  control through MCP. Control uses existing native actions and Real Activity Monitoring evidence; actual
  application effects require separate assertions.
- TCs reference meaning IDs separately from TC IDs. Example: TC-030 references
  HPE990.Setup.Preferences.General.Language. Its current HWND and UI ID are resolved
  from the verified target map, never copied into TC procedure text.
"""

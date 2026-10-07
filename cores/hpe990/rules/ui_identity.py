"""Canonical UI element identity management requirement."""

RULE_ID = "HPE990_UI_IDENTITY_SSOT"
TITLE = "Manage all collected UI identities in one registry"
SOURCE = "cores/hpe990/rules/ui_identity.py"
STATUS = "active"
BODY = """
- Assign every collected native, accessibility and visual element an internal UI ID.
- Scope includes every observed screen, window, modal, popup, menu, button,
  input and other UI element, including children inside modals and popups.
  Assign IDs when elements are first collected; unopened or unobserved UI remains
  uncollected and must not be reported as having complete ID coverage.
- Use ui_id as the internal identity reference. Connect native children through
  parent_ui_id and accessibility/visual elements to their containing window through
  root_ui_id. A modal or popup is an identity-bearing element itself, not merely
  a screenshot or a label for its child controls.
- Popups without a separate HWND still require IDs for elements observed through
  accessibility or visual collection. Preserve provider evidence and unresolved
  identity scope; do not invent a native HWND or an unobserved popup container.
- Store identities in the family-local paths-defined SQLite registry. Allocate
  UI-000001 style monotonically increasing IDs transactionally; never recycle IDs.
- HWND, provider IDs, positions and screenshots are observation evidence, not global IDs.
- Reuse unique fully named native ancestry across observations and sessions;
  preserve unnamed/ambiguous and unlinked provider identities as session scoped.
  Do not claim session-scoped IDs survive recreation or prove handle reuse identity.
- Link visual/accessibility evidence to native identity only with unambiguous,
  same-process, same-root evidence. Unverified semantic states remain unverified.
- Expose canonical definitions and observations through public MCP collection/catalog.
  Preserve original evidence when indexing historical snapshots.
- Examples: a uniquely matched Backup Date frame and native control share UI-000123;
  two unnamed sibling widgets receive separate IDs, with unresolved identity scope.
  A collected confirmation modal UI-000200 and its OK button UI-000201 each have
  an ID, with the button's parent_ui_id pointing to UI-000200. A visual-only popup
  element UI-000202 has root_ui_id pointing to its observed containing window,
  hwnd=null and identity_scope=session_observation until stronger identity is verified.
- Back up the SQLite registry with collected evidence. Removing it loses identity
  continuity; evidence directories alone are not the identity allocation authority.
"""

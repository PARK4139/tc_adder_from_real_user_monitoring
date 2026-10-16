"""Local destination override for the common one-shot publication contract."""

RULE_ID = "HPE990_ONE_SHOT_OUTPUT"
TITLE = "auto_emulator one-shot output"
SOURCE = "cores/hpe990/rules/one_shot_output.py"
STATUS = "active"
BODY = """
- Basis: user directive 2026-10-12; follow pk_system common one-shot rules.
- Override the common deployment directory/basename only: publish under the
  parent 3rd_party directory as auto_emulator_X.Y.exe, with two integer components.
- The fixed runtime path is auto_emulator.exe in the same directory. Keep it stable.
- Build intermediates live under D_TEMP/hpe990/build; issue verification evidence
  lives under D_TEMP/hpe990/evidence/{issue-id}/{run-id}.
- Automatically reserve monotonic versions using configs/releases.json under
  a cross-process lock. Record successful releases only after candidate and
  destination verification. Never overwrite a released version.
- Launchers resolve paths independently of cwd, validate prerequisites, use uv,
  and propagate nonzero exit codes. Preflight BDD before version allocation.
- No BDD at this milestone is NOT_APPLICABLE with a reason, never BDD PASS.
"""

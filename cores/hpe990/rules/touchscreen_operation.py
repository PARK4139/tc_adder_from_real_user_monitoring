"""User-facing interaction contract for the touchscreen Emulator."""

RULE_ID = "HPE990_TOUCHSCREEN_OPERATION"
TITLE = "Touchscreen controls in UI collection and review TCs"
SOURCE = "cores/hpe990/rules/touchscreen_operation.py"
STATUS = "active"
BODY = """
- HPE990 emulates a touchscreen application. Collect and author user workflows using
  observed on-screen controls through public auto_emulator MCP.
- Close numeric and text input modals by clicking their observed on-screen ↵ button.
  Keyboard ESC or Enter is not the user operation or its acceptance evidence.
- ↵ confirms the input buffer; do not describe it as Cancel. During observation-only
  collection, leave the original buffer unchanged and do not Save Preferences.
- Use observed touch controls to dismiss selectors and Cancel Preferences. Verify the
  resulting window state; successful input delivery alone is not application success.
- Preserve historical keyboard observations as supplemental evidence, separately from
  touchscreen validation. An unresolved touch control remains explicitly unverified.
- Example Steps: PD 선택 / 화면 숫자 버튼으로 시험값 입력 / ↵ 버튼 클릭.
  Expected Result: PD에 입력한 시험값이 보여야 합니다.
- Save/reopen and actual functional behavior require their own execution evidence;
  collecting a keypad or writing a draft TC does not establish those outcomes.
"""

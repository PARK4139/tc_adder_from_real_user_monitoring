"""Canonical requirement for MCP coverage of HPE990 Emulator operations."""

RULE_ID = "HPE990_MCP_FUNCTION_COVERAGE"
TITLE = "Expose every Emulator operation through MCP"
SOURCE = "cores/hpe990/rules/mcp_function_coverage.py"
STATUS = "active"
BODY = """
## Requirement
- Basis: user directive, 2026-10-06: Emulator의 모든기능은 mcp 로 구현해야합니다.
- Every Emulator operation must be available through callable MCP tools,
  including lifecycle, UI interactions, Real Activity Monitoring, collection, telemetry, and analysis.
- Derive the complete product-operation inventory from observed UI analysis;
  do not assume the current backlog lists every Emulator function.
- Host the family protocol adapter at cores/hpe990/mcp/server.py with tool
  groups in cores/hpe990/mcp/tools/. Keep the server thin and use family-owned
  Python/Rust implementations. Manage Python dependencies and execution with uv.
- Register the implemented server in project-local .mcp.json using a portable
  uv launcher. Do not register nonexistent implementations.
- BDD automation must invoke the same public MCP tools used by clients.
  Real Activity Monitoring must remain active during tool execution and session shutdown.
- TC의 수행 절차뿐 아니라 기대 결과의 관측과 판정도 public MCP tool로 설계한다.
  각 Step은 조작 호출, 결과 관측 호출, 기대값과 실제값을 비교하는 판정 호출을 연결한다.
  공통 관측·판정 도구를 재사용하고 TC마다 동일 기능의 도구를 중복 생성하지 않는다.
- 판정 조건은 대상 UI ID 또는 의미 경로, 관측 속성, 비교 연산, 기대값, 허용 오차와
  대기 제한을 명시한다. TC의 기대 결과를 정본으로 사용하며 별도 사본을 수동 관리하지 않는다.
  예: 표시 여부, 선택값, 문구, 팝업 종료, 저장 후 재진입 값, 원래 값 복구 상태.
- 판정 도구는 session_id, TC ID, Step 번호, 기대값, 실제 관측값, 판정 근거,
  관측 시각과 증거 경로를 구조화해 반환한다. 관측은 해당 조작 이후의 동일 세션 자료를 사용한다.
  값·상태의 안정화를 제한 시간 안에 관측하고, 필요한 Real Activity Monitoring 기록을 함께 연결한다.
- 입력 전달 성공, 도구 호출 성공 또는 스크린샷 생성 성공만으로 기대 결과를 PASS 처리하지 않는다.
  조건을 만족한 관측 증거가 있을 때만 PASS, 확인된 불일치는 FAIL로 판정한다.
  명세 미확정, 관측 수단 부재, 대상 식별 불가 또는 호출 오류는 별도의 미판정 상태와 이유로 반환한다.
  미판정 결과는 필수 BDD의 통과로 집계하지 않는다.
- 소리·LED·실장비 가공·통신처럼 화면값만으로 확인할 수 없는 기대 결과는 필요한 실제
  관측 수단과 MCP 인터페이스를 정의한다. 관측 수단이 없으면 해당 효과를 검증했다고 보고하지 않는다.
- Verify discovered tool schemas and actual MCP calls, not only direct function
  calls. Each operation needs a tool mapping and observed expected/actual evidence.
- Completion requires 100% coverage of the verified operation inventory, zero
  unmapped operations, and zero failed required tool-call acceptance checks.
  Unexplored functions remain explicitly unresolved; do not claim full coverage.
- Remote telemetry transmission remains future work; record locally now.
"""

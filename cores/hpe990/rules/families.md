# families — hpe990

| function family | meaning | implementation location |
|---|---|---|
| lifecycle | HPE990 실행 대상 식별과 세션 실행·종료 | `cores/hpe990/functions/`, `cores/hpe990/wrapper/` |
| activity_monitoring | Real Activity Monitoring | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_collection | 창·모달·컨트롤 UI 수집 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| telemetry | 창/UI 변화의 구조화된 이벤트 기록 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_analysis | UI 상태·전이 및 제어 식별자 분석 | `cores/hpe990/docs/`, `cores/hpe990/functions/` |
| bdd | pytest-bdd 시나리오와 RAM 병행 자동제어 | `cores/hpe990/tests/`, `cores/hpe990/functions/` |
| mcp | 모든 Emulator 기능의 MCP 노출·계약·호출 검증 | `cores/hpe990/mcp/server.py`, `cores/hpe990/mcp/tools/` |

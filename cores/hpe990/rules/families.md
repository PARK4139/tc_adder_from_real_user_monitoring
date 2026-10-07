# families — hpe990

| function family | meaning | implementation location |
|---|---|---|
| lifecycle | HPE990 실행 대상 식별과 세션 실행·종료 | `cores/hpe990/functions/`, `cores/hpe990/wrapper/` |
| activity_monitoring | Real Activity Monitoring | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_collection | 창·모달·컨트롤 UI 수집 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_mapping | 버전별 내부 UI 이름·의미 ID·세션 ID 매핑 및 검증 | `cores/hpe990/functions/`, `cores/hpe990/configs/`, `cores/hpe990/mcp/`, `cores/hpe990/tests/` |
| ui_control | 식별된 UI의 마우스·키보드·입력값·OCR 기반 조작과 유지보수 기능 제어 | `cores/hpe990/functions/`, `cores/hpe990/rust/`, `cores/hpe990/mcp/`, `cores/hpe990/tests/` |
| telemetry | 창/UI 변화의 구조화된 이벤트 기록 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_analysis | UI 상태·전이 및 제어 식별자 분석 | `cores/hpe990/docs/`, `cores/hpe990/functions/` |
| bdd | pytest-bdd 시나리오와 RAM 병행 자동제어 | `cores/hpe990/tests/`, `cores/hpe990/functions/` |
| tc_review | 검수 TC 파일 정본과 실시간 검수 웹 | `cores/hpe990/docs/bdd/`, `cores/hpe990/functions/`, `cores/hpe990/scripts/`, `cores/hpe990/tests/` |
| mcp | 모든 Emulator 기능의 MCP 노출·계약·호출 검증 | `cores/hpe990/mcp/server.py`, `cores/hpe990/mcp/tools/` |
| diagnostics | 검증 도구·BDD 준비 조건·테스트 기준의 진단과 결과 추적 | `cores/hpe990/tests/`, `cores/hpe990/functions/`, `cores/hpe990/issues/` |

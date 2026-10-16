# families — hpe990

| function family | meaning | implementation location |
|---|---|---|
| lifecycle | HPE990 실행 대상 식별과 세션 실행·종료 | `cores/hpe990/functions/`, `cores/hpe990/wrapper/` |
| activity_monitoring | UI observation: 기존 Real Activity Monitoring 기반 창·화면 변화와 수집 상태 관측 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| observability | UI Automation & Observability 책임 경계와 관측 상태 조회 | `cores/hpe990/functions/observability.py`, `cores/hpe990/mcp/tools/observability.py` |
| rum | 실제 사용자 성능·오류 계측 책임; 현재 계측 미구현 상태 조회 | `cores/hpe990/functions/rum.py`, `cores/hpe990/mcp/tools/observability.py` |
| ui_collection | 창·모달·컨트롤 UI 수집 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_mapping | 버전별 내부 UI 이름·의미 ID·세션 ID 매핑 및 검증 | `cores/hpe990/functions/`, `cores/hpe990/configs/`, `cores/hpe990/mcp/`, `cores/hpe990/tests/` |
| ui_control | 식별된 UI의 마우스·키보드·입력값·OCR 기반 조작과 유지보수 기능 제어 | `cores/hpe990/functions/`, `cores/hpe990/rust/`, `cores/hpe990/mcp/`, `cores/hpe990/tests/` |
| telemetry | 창/UI 변화의 구조화된 이벤트 기록 | `cores/hpe990/functions/`, `cores/hpe990/rust/` |
| ui_analysis | UI 상태·전이 및 제어 식별자 분석 | `cores/hpe990/docs/`, `cores/hpe990/functions/` |
| bdd | HPE990 실행 대상을 통한 도구 검증 카탈로그·추적표 연동; 도구 검증 시나리오 정본은 auto_emulator family 소유 | `cores/hpe990/functions/`, `cores/auto_emulator/tests/bdd/` |
| tc_review | 검수 TC 파일 정본과 실시간 검수 웹 | `cores/hpe990/docs/bdd/`, `cores/hpe990/functions/`, `cores/hpe990/scripts/`, `cores/hpe990/tests/` |
| mcp | 모든 Emulator 기능의 MCP 노출·계약·호출 검증 | `cores/hpe990/mcp/server.py`, `cores/hpe990/mcp/tools/` |
| mcp_server_management | loopback HTTP MCP 서버 시작·종료·재시작 | `cores/hpe990/mcp/tools/server_manager.py`, `cores/hpe990/mcp/server.py` |
| diagnostics | 검증 도구·BDD 준비 조건·테스트 기준의 진단과 결과 추적 | `cores/hpe990/tests/`, `cores/hpe990/functions/`, `cores/hpe990/issues/` |

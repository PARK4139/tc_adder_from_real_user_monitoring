# Real Activity Monitoring 기반 UI 수집

Edger 하위 화면 수집은 지속 실행 중인 RAM의 실제 관측 기록을 기본 증거로 사용한다. MCP 제어 전후 inventory는 요소 목록과 탐색 경로를 보완한다.

## 수집 절차

1. 공개 MCP `hpe990_ram_status`와 `hpe990_ram_semantic_status`로 native Real Activity Monitoring 활성, semantic Real Activity Monitoring `sampling_healthy`, timestamp activity logger 활성을 확인한다.
2. 공개 MCP로 화면·모달·팝업을 탐색한다. 터치 화면의 실제 버튼으로 이동·복귀한다.
3. `hpe990_ram_semantic_read`와 `hpe990_telemetry_read`로 이벤트를 조회한다. 각 스트림의 session/run/sequence를 유지한다.
4. 화면 등장·변화·소멸 이벤트의 시각, UI ID, HWND, 원본 PNG 및 전후 snapshot을 보관한다.
5. 탐색 action_id와 Real Activity Monitoring 관측 구간을 연결한다. 시간 일치는 동작 원인이나 기능 PASS의 증명이 아니다.

## 판정

RAM이 활성이라는 응답만으로 해당 화면 수집을 판정하지 않는다. 실제 Real Activity Monitoring 이벤트와 이미지·요소 증거를 확인한다. 이벤트 없는 구간, `observation_gap`, 캡처 실패와 읽을 수 없는 값은 명시한다. OCR은 미검증 관측으로 유지한다. 샘플 간 순간 변화와 가려진 화면은 누락될 수 있다.

미탐색 경로와 권한이 필요한 화면은 전체 수집 완료로 처리하지 않는다. Emulator와 RAM은 탐색 이후에도 유지한다.

## 실제 확인: 2026-10-08

- 세션: `dbe3d24e98a64902afdc0b4109d670a1`
- Semantic Real Activity Monitoring run: `91158e8edeca4442a9bb46050b5700e3`
- 공개 MCP 조회 시점까지 해당 run 이벤트 3,141개. 기존 관측 공백 13개도 보존했다.
- 이번 Edger frontier 탐색 제어 133건 모두 Real Activity Monitoring 활성. 117건의 시간 구간에서 이벤트 관측, 나머지 16건은 이벤트 없는 구간으로 기록했다.
- 연결된 증거 파일 776개 존재 확인. 조회 시점 semantic 관측 상태 정상, native Real Activity Monitoring 및 timestamp logger 활성.
- 증거: `{D_TEMP}/hpe990/evidence/50c688e3/edger-frontier-resume/ram-collection-report.md`, `ram-collection-index.json`, 공개 MCP 원본 응답.

이 확인은 Real Activity Monitoring 기록과 탐색 증거 연결에 대한 확인이다. 모든 화면 수집 또는 기능 시험 완료 판정은 아니다.

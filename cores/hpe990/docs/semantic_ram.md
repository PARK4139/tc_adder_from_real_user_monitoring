# 입력값·문구·색상 변화 RAM

소스 uv MCP에 추가한 관찰 기능입니다. 기존 WinEvent/Rust RAM과 병행하며
MCP 연결 종료 후에도 실행됩니다. 배포 EXE는 갱신하지 않았습니다.

## 실행과 조회

1. `hpe990_status` 또는 `hpe990_launch`에서 현재 `session_id` 확인.
2. `hpe990_ram_semantic_start`에 `session_id` 전달. 기본 요청 주기 250ms,
   접근성 `msaa`; `uia`, `none`도 지원. 이미 실행 중이면 기존 설정 반환.
3. `hpe990_ram_semantic_status`에서 실제 관찰 간격, 처리 시간, 최근 증거 확인.
4. `hpe990_ram_semantic_read`의 `after_sequence`로 새 이벤트 조회.
5. `hpe990_ram_semantic_stop`으로 추가 관찰기만 정리. 기존 RAM과 앱은 유지.

## 기록 내용

- Rust RGB 비교는 임계값 0: 한 픽셀의 한 채널이 1만 달라도 감지.
- 변경 영역, 픽셀 수, 최대 채널 차이, RGB 전후 예시, 전후 원본 PNG 보관.
- 루트 `ui_id`와 변경 영역에 겹치는 컨트롤의 SSOT ID 연결.
  겹침은 후보 연관이며 해당 컨트롤의 의미상 변경 확정이 아님.
- HWND 문구·상태, 읽힌 접근성 값·문구, OCR 입력란 내용·문구 비교.
  OCR 등장·소멸도 기록하며 `semantic_state_verified: false` 유지.
- 같은 이미지는 기존 PNG 재사용. 동일 관찰은 증거 스냅샷 재사용.
- `observation_gap`은 캡처/OCR/접근성 실패. 실패 전후를 정상 연속 비교로 처리하지 않음.
- 원문과 이미지는 가족 runtime의 `semantic-ram/{session_id}/{run_id}/`에 로컬 기록.
  기존 Rust `events.jsonl`과 분리된 순번·세션·run 식별자를 사용.

## 관찰 범위

성공적으로 캡처한 가시 최상위 창·모달·팝업과 그 안의 픽셀을 비교합니다.
접근성 값은 기본 5초 간격으로 별도 시도하며 요청은 1초에 제한합니다.
OCR은 이미지가 바뀌거나 이전 인식이 실패했을 때 재시도합니다.
실제 주기는 캡처·OCR 처리 시간에 좌우되고 상태에 기록됩니다.
기존 Rust RAM의 100ms 요청 주기 감지도 병행됩니다.
짧게 나타났다 사라지는 변화, 가려짐·최소화·캡처 실패, 읽을 수 없는 값까지
모두 수집한다는 보장은 없습니다. 전체 UI 완료 판정은 별도 미해결 항목입니다.

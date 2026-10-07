# UI 탐색 현황

정본 이슈: `issues/working/ui_collection/complete-ui-inventory/50c688e3.md`.
전체 UI 탐색은 완료되지 않았다. 공개 MCP 요청 성공과 실제 기능 검증을 구분한다.

## 현재 확인한 경로

2026-10-07 세션 `5a6c0a26ee604ff58eb87bc12bbfcba7`, 설치된 CIRCLE 샘플 기준.

| 경로 | 확인한 결과 |
|---|---|
| 실행 > Continue > Edger | 초기 화면, 작업 없는 상태 |
| Edger > 폴더 버튼 > Job Manager | 설치 샘플 목록 및 선택 상태 |
| CIRCLE 선택 > 불러오기 > Edger | 작업 번호와 도형 표시 |
| 좌측 하단 패널 상단 선택 버튼 | 아이콘 선택 QPopup, Escape 복귀 |
| 좌측 하단 패널 두 번째 선택 버튼 | 다른 아이콘 선택 QPopup, Escape 복귀 |
| Size 입력 | 숫자 키패드, 원래 0.00 유지 및 확인 버튼으로 복귀 |
| 우측 옵션 선택 버튼 | QPopup, Escape 복귀 |
| 우측 표시 모드 버튼 | inline 아이콘 변화, 재클릭 후 원래 Edger PNG 해시 복원 |
| Edger > Job Editor | 편집 화면 및 입력·선택 요소 |
| Job Editor > PD | 64.0, 범위 30.0~99.0 키패드; 원래 값 유지 후 복귀 |
| Job Editor > Cancel | 작업 로드 후 Edger PNG 해시 복원 |
| Edger > Digital Pattern | 회전·한쪽 변형·크기 조정·편집 모드별 화면, Notification 도구 창 |
| Digital Pattern > Hole Editor | HoleEditor 화면 및 요소 |

아이콘 선택 항목의 의미는 사양으로 확정하지 않았다. 도형을 변경하는 드래그와 저장 동작은 이번 탐색에 포함되지 않았다.

## 증거 조회

`{D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/`:

- `calls.jsonl`: timestamp, 공개 MCP 요청·응답, action ID, RAM 상태.
- `transitions.json`: action별 전후 수집 경로, 보이는 창 관계, 변경 PNG.
- `acceptance.json`: 실제 호출 수, RAM 활성, 미탐색 여부.
- `hpe990_ui_catalog-final.json`: UI ID별 관찰·요청 기록 및 이름 기준 미탐색 후보.
- 각 응답이 가리키는 `inventory.json`: native/접근성/시각 요소와 이미지 연결.

## 남은 범위

- Edger와 각 편집 화면의 나머지 버튼·입력란 및 조건별 화면.
- 드릴 데이터가 필요한 Hole Editor 입력과 팝업, Scan & Cut 흐름.
- 이름 없는 요소의 실제 유형과 역할 검증. 이름 기준 버튼 목록은 전체 interactive 목록이 아니다.
- Maintenance 정상 진입 절차: 별도 차단 이슈 `79ec55b7`.
- 설정·가공 조건별 기능 동작 및 pytest-bdd 실행. 이번 화면 탐색 결과를 기능 PASS로 취급하지 않는다.

팝업 이미지 누락은 `134f37f3`, 과거 UI ID 중복 등록 보완은 `9a96ea1f`에서 추적한다. 배포 EXE는 갱신하지 않았다.

# Preferences 나머지 탭 검수 TC

2026-10-07~2026-10-08, HPE990 GUI 1.22.0의 공개 auto_emulator MCP로 General 외 현재 노출된 6개 탭을 수집했다. 창 이미지·OCR·HWND·접근성·UI ID 관측을 보존하고, 스크롤 영역은 상단부터 최하단까지 겹치는 구간으로 확인했다.

| Suite | 설정 요소 | 추가 TC | ID 범위 |
|---|---:|---:|---|
| Setup > Preferences > Layout | 17 | 21 | TC-290~TC-490 |
| Setup > Preferences > Edging | 59 | 63 | TC-500~TC-1120 |
| Setup > Preferences > Digital Pattern | 2 | 5 | TC-1130~TC-1170 |
| Setup > Preferences > Hole Editor | 11 | 14 | TC-1180~TC-1310 |
| Setup > Preferences > Frame Fitting | 13 | 17 | TC-1320~TC-1480 |
| Setup > Preferences > Comm. Port | 16 | 20 | TC-1490~TC-1680 |
| 합계 | 118 | 140 | 10 단위 증가 |

정본은 `sqa/tc/to_review/setup/preferences/{tab}/TC-숫자.feature`다. 탭 진입·스크롤·요소별 설정·Save·Cancel을 분리하고, 각 TC에 사전 조건과 복구 절차를 둔다. General 및 Edger의 기존 ID는 유지한다. 검수 순서는 General 다음 위 표의 탭 순서, 이후 Edger다.

- 공유 검수: <http://172.20.13.185:9999/tc-up-validation/>. 파일 변경을 기존 서버가 감지하며 재시작하지 않는다.
- 수집 증거: `{D_TEMP}/hpe990/evidence/66c80f85/collection-report.json`. 탭별 이미지 경로·해시·시각·스크롤 범위·요소 관측 ID 포함.
- 작성·검증 증거: 같은 디렉터리의 `authoring-report.json`, `authoring-validation.json`, `review-tests.xml`, `shared-review.html`.
- 재수집 요청 묶음은 `scripts/preferences_capture.py`로 공개 MCP를 호출해 기록할 수 있다. `--requests` JSON과 외부 family 증거 루트 아래의 `--evidence-directory`를 지정한다. 기존 기록 덮어쓰기는 거부한다.

## 미확정 범위

TC는 미실행 초안이다. 숫자가 보이는 필드도 개별 편집 가능 여부와 실제 입력유형을 확인하기 전 `(입력란)`으로 작성했다. 입력유형·허용 형식/범위·시험값·미개방 선택 목록·저장 규칙은 구체적인 칩으로 구분한다. Hole Editor 상단 무라벨 필드도 포함했다. 미개방 팝업과 실제 장비 동작의 전체 수집·시험 완료를 의미하지 않는다.

수집 중 설정값을 변경하거나 Save를 누르지 않았다. Preferences를 Cancel로 닫고 원래 Setup으로 복귀했으며 기존 Emulator 세션·Real Activity Monitoring·timestamp 로그·검수 서버를 유지했다.

## 개별 팝업 수집과 순차 TC 갱신

2026-10-08 재수집은 선택기 19개와 입력란 59개를 대상으로 각 팝업을 연다. 전후 inventory, 원본 PNG, UI ID·HWND, MCP action_id와 시각은 `{D_TEMP}/hpe990/evidence/50c688e3/preferences-recollect/`에 보존한다. 완료 결과와 제한은 해당 폴더의 `collection-report.json` 및 `report.md`에서 확인한다.

사용자 조작 기준은 `rules/touchscreen_operation.py`다. 숫자 모달은 화면의 ↵ 버튼 클릭으로 확정하며 ESC·Enter 키를 TC의 사용자 조작으로 작성하지 않는다. 초기 키보드 닫기 관측은 보조 증거로만 유지한다. ↵는 취소가 아니므로 관찰 수집에서는 현재 버퍼를 유지하고 Preferences의 Save를 누르지 않는다.

Machine ID는 영문·숫자 화면 키보드로 확인해 `(문자 입력란)`으로 작성한다. BARCODE Baud Rate 목록은 BARCODE를 일시적으로 체크한 후 수집하고 체크 해제 및 Cancel로 복구한다. The Number of Radii의 첫 빈 이미지는 추가 수집으로 선택 목록을 확보하되 최초 기록도 보존한다.

수집 직후 기존 `to_review` 파일을 갱신한다. 관찰된 숫자 모달은 `(숫자 입력란)`과 터치 Steps를 반영하고, 저장·재진입·실동작 미검증은 유지한다. TC-360 PD는 원본 이미지에서 확인한 표시 범위 30.0~99.5를 포함한다. TC-1190의 이전 무라벨 입력란은 실제 팝업 제목 `Hole Depth (0=Through Hole)`로 갱신한다. TC ID를 새로 발급하거나 `reviewed` 파일을 변경하지 않는다.

반복 수집에서는 공개 MCP `hpe990_ui_collect` / `hpe990_ui_control`의 `refresh_templates=false`로 종합 초안 내보내기만 보류할 수 있다. 이미지·HWND·UI ID 등록과 Real Activity Monitoring 기록은 유지된다. 탐색 마지막에 `hpe990_tc_templates`를 호출해 종합 카탈로그를 갱신한다. 기본값 `true`는 기존 동작을 유지한다.

`hpe990_tc_templates(summary_only=true)`는 전체 JSON/HTML을 생성한 뒤 개수·파일 경로만 MCP로 반환한다. 누적 증거가 큰 세션에서 전체 초안 목록을 전송하지 않고도 완료 기록을 확보할 수 있다.

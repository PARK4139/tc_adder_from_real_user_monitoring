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

아래의 초기 탐색 목록과 이후 추가 탐색을 함께 확인한다. 최신 추가 증거는
`{D_TEMP}/hpe990/evidence/50c688e3/edger-frontier-resume/report.md`와
`ram-collection-report.md`에 있다. 2026-10-08 추가 탐색 누적 제어 208건,
inventory 666개, 관측 UI ID 9,691개, 창 인스턴스 57개, PNG 상태 202개를
확인했다. 전체 프로그램의 화면 수 또는 수집률 분모로 사용하지 않는다.

### 최신 추가 경로: MCP 제어 및 실제 RAM 기록

| 경로 | 추가 증거 |
|---|---|
| Edger > edging type | 8개 선택과 조건별 Manual 진입 |
| Bevel Height Editor | 일반/mini 조건, 방향별 값, Front Height/Width와 취소창 |
| Step Bevel / Deep Step Bevel | Full/Partial, 방향별 값, Front Width, Groove Depth/Width, Front Grooving Position |
| Step Bevel > Semi T Bevel | 별도 Dlg_SemiTEditor, 위치·높이·ANGLE 모달, 종료 확인 |
| Step Bevel > Partial Grooving | 두 arc 구간과 각 입력 모달, 취소 확인 |
| Edger > Groove 편집 > Partial Grooving | 별도 진입, 5개 형상, Start/End Angle·Depth·Width, 하위 옵션·확대 및 취소 |
| Edger 메인 | PL/PC/HI/TR, 3개 profile, 6개 위치 선택, 좌우 렌즈·잠금 |
| Digital Pattern | Percent 모달, 좌우 렌즈·연결·확대·시험 버퍼 Reset |
| 작업 다시 불러오기 | FIELDJACKET_M 처리 목록 선택 및 Edger 복귀 |

숫자 모달은 원래 값을 유지하고 실제 ↵ 버튼으로 닫았다. Native RAM에서
208건 모두 action_id의 requested/observed 마커를 확인했다. Semantic RAM은
조회 시점 누적 이벤트 4,785개이며, 190건의 제어 시간 구간에서 이벤트를
관측했다. 18건의 빈 구간과 접근성 공급자 시간 초과 등 관측 공백 20개도
보존한다. 연결 증거 파일 1,182개 존재 및 체크포인트 19개 해시 일치를
확인했다. 요청 마커·시간 연결·관측값을 기능 PASS로 취급하지 않는다.

원본 JOB/DR 파일은 보존했다. 시험 작업의 처리 레코드에는 Groove 상태가
남아 있으며 재로드 PNG와 복귀 직전 PNG가 일치한다. 최초 Deep Step 상태의
작업 버퍼/DB 전체 복구를 주장하지 않는다. Maintenance 정상 진입,
장비·데이터 조건별 경로와 숨겨진 Adjustments 페이지의 실제 진입은
미확인이다. 전체 UI 수집 이슈는 완료 처리하지 않는다.

- Edger와 각 편집 화면의 나머지 버튼·입력란 및 조건별 화면.
- 드릴 데이터가 필요한 Hole Editor 입력과 팝업, Scan & Cut 흐름.
- 이름 없는 요소의 실제 유형과 역할 검증. 이름 기준 버튼 목록은 전체 interactive 목록이 아니다.
- Maintenance 정상 진입 절차: 별도 차단 이슈 `79ec55b7`.
- 설정·가공 조건별 기능 동작 및 pytest-bdd 실행. 이번 화면 탐색 결과를 기능 PASS로 취급하지 않는다.

팝업 이미지 누락은 `134f37f3`, 과거 UI ID 중복 등록 보완은 `9a96ea1f`에서 추적한다. 배포 EXE는 갱신하지 않았다.

## Edger 하위 추가 탐색 (2026-10-08)

세션 `dbe3d24e98a64902afdc0b4109d670a1`, GUI 1.22.0. 공개
`auto_emulator MCP` stdio 도구로 실행·Continue 후 수집했다. Native RAM,
semantic RAM, timestamp 병렬 로그를 유지한다. 이번 입력 모달은 원래 값을
유지하고 화면의 ↵ 버튼으로 닫았다. 과거 Escape 관찰과 구분한다.

증거 정본: `{D_TEMP}/hpe990/evidence/50c688e3/edger-remaining/`.
`transitions.jsonl`에 action ID와 전후 inventory, `numeric-field-audit.jsonl`에
입력 UI ID와 실제 모달 제목, 원본 MCP 응답에 provider 진단을 보존한다.
`report.md`/`acceptance.json`은 최종 집계 시 갱신한다.

| 경로 | 실제 관찰 |
|---|---|
| Edger ?? | PD??? IPD?Delta Y?DBL?FPD ? Size ??, ?? Curve ??; Lens Diameter / Blocking Position ??, Job Number ???, ?? ?? New ??? ??? ?? ?? |
| Job Editor | PD, 양안 IPD·높이·Delta Y, DBL, FPD, Clamp 입력 모달; curve/tilt 편집 창과 입력 모달 |
| Digital Pattern | Scale·One Side·Rotate·Edit 모드, 입력 모달, Confirm Apply의 No로 복귀 |
| Hole Editor | Hole/Slot 추가 팝업, START/END X·Y, Diameter·Depth·Angle, Easy Move 및 Hole Preset의 SET/SAVE/LOAD 화면 |
| Setup > Statistics | Current·Wheel·Total 탭 전환; Current 하단 스크롤 |
| Setup > Date/Time | 월 선택 팝업, 연도 inline 편집, 날짜·시각 입력 모달 6개; Apply 사용하지 않음 |
| Setup > Configuration Management | Restore 파일 선택 창에서 Cancel, Backup 파일명 키보드와 실제 백업 생성 |
| Setup > Touchscreen Check | 화면 터치 반응과 화면 내 닫기 버튼 |
| Setup > Adjustments | General, Rotation, Clamp, Size, Margin, Axis, Bevel/Groove, Safety Bevel, Step Bevel, Drilling, Wheel, Control의 12개 탭 실제 진입 |
| Adjustments 입력 모달 | Rotation 29, Clamp 12, Size 12, Margin 20, Axis 20, Bevel/Groove 11, Safety Bevel 16, Step Bevel 6; 각 scroll area 끝 확인. Drilling의 Hole Diameter, Wheel 입력 2개, Control의 Door Safety Current Value도 확인 |
| Adjustments > General > Lens Adaptor | 선택 목록 8개; User Defined 선택 후 Width·Height 숫자 모달. 원래 Wide로 복원하고 Adjustments Cancel |
| Setup > Test Mode | Sensor, X/Y/R, Feeler, SBG/Wheel, Pump, Clamp/Window, Drill, PI/MOTOR 8개 탭 진입; PI/MOTOR 하단은 별도 스크롤 수집 |
| Test Mode > Drill > Replace Drill Bit | 대기 모달 후 교체 안내 이미지·문구·Cancel 버튼 확보, Cancel 복귀 |
| Test Mode > Pump > Water Nozzle Adjustment | 안내 문구·이미지·Close 버튼 확보 및 복귀 |
| Setup > Wheel Dressing | Main Wheel/Safety Beveling 선택 상태와 Dressing Time 요소; Start 요청 후 새 화면 없음, 원래 Main Wheel 복원 및 Close |
| Setup > Calibration | Feeler 선택/복원, Hall Sensor Contact Calibration 시작 안내에서 Cancel, Developer 명령 입력 창에서 Cancel. 교정 및 명령 실행은 하지 않음 |

### 변경 및 미확인 범위

- Backup 키보드의 빈 값 ↵는 닫히지 않았다. 수집을 이어가기 위해
  `UI_COLLECTION_1791424855`를 입력해 새 CFG를 생성했다. 기존
  `hpe_990pro.exe.cfg` 해시도 변경되었다. 변경 내용을 해시만으로 단정하지
  않는다. `config-hashes-before.json`, `config-hashes-after.json`,
  `backup-artifact.json`과 백업 파일 사본을 보존한다.
- Hole Preset LOAD와 임시 Hole 추가는 작업 버퍼를 변경했다. 원본 JOB/DR
  파일과 작업 버퍼를 구분하며, 탐색 종료 시 원본 샘플을 다시 불러온다.
- Scan & Cut, Factory Reset, Software Upgrade GUI/MOTOR 버튼은 이번 조건에서
  새로운 화면이 열리지 않았다. 요청 전달 성공을 기능 PASS로 처리하지 않는다.
- Maintenance의 앱 표시값 확인은 Setup으로 돌아왔으며 내부 화면을 열지
  못했다. 정상 진입 절차가 필요하다. 접근 코드 추측은 수행하지 않는다.
- Notification의 PrintWindow 성공 PNG가 단색인 증거가 발견되었다. QTool/
  QPopup 단색 캡처 원본 보존과 BitBlt 대체·품질 진단을 추가했으나, 실제
  Notification은 Water Nozzle Adjustment 진입 때 실제 MCP에서도
  `uniform_pixels_after_fallback`으로 남았다. 문구 확보는 미충족이다.
  Lens Adaptor의 테두리만 그려진 빈 QPopup도 발견되어 3px 테두리를
  제외한 내용 영역 검사를 추가했다. 재수집한 선택 목록의 문구는 확보했다.
  실행 중인 semantic RAM은
  기존 코드를 유지하므로 신규 MCP 수집의 보완과 구분한다.
- Adjustments는 우측 화살표 반복 시 Control에서 이동이 멈췄다. 숨겨진
  Compensation·Calibration·QC 페이지 HWND는 실제 진입 증거가 아니다.
  Wheel 첫 클릭 후 수집은 Drilling 상태였으나 재확인에서 Wheel 진입을
  확보했다. 빠른 요청 직후의 상태만으로 접근 불가 판정을 내리지 않는다.
- Test Mode의 X/Y/R·Drill Move 및 Clamp Pressure 클릭에서는 이번 조건에서
  숫자 모달이 열리지 않았다. 센서 표시값과 조작 성공을 추정하지 않는다.
- Statistics의 Wheel/Total 하단 및 Edger의
  조건별 화면을 계속 탐색한다. 전체 UI 완료 및 BDD 실행 PASS는 미충족이다.

### ??? Single Vision ???

?? semantic RAM??? Notification(`UI-000009`)? ????? ???
????? ??? ??? ? ??? ??? ?????. Job Manager?
?? `Single Vision` OCR(`UI-036691`)? ??? ??? ???? ???.

?? MCP? ?? ??? ??? `Single Vision` ??? PNG? OCR
`UI-057992`? ????. action `cbb41f8d111745dc98fbc93f9df53101`?
?? inventory `34fe593d2c174b2496586607d41ca89f`? ????.
semantic RAM? ?? stop/start? ? ??? ????? native RAM?
activity timestamp ??? ????. ?? semantic stream? ????
???. ??? ?? ??~? ? ?? ?? ? 4.6? ??? ????.

? run `91158e8edeca4442a9bb46050b5700e3`??? ??
`hpe990_ram_semantic_read`? ??? ????OCR?visible ?? ? ??
???? ????. `single-vision-verified-ram.json`? ?? ???
????. OCR? `semantic_state_verified=false`? ????.
?????????? ?? ?? ??? ?? ?? ??? ?? ???
???? ???.

?? ???/? ?? ??? ????? ?? ??? ??? ????.
UI ID ??? RAM ??? ???? ?? ?? ? ??
`hpe990_tc_templates`? ????. ????? ?????? ?? ???
29? PASS? Ruff PASS. ?? ?? ?? ???? 146 PASS/1 FAIL??
?? ?? ?? ? ?? ???? ?? ??. BDD ?? ??? ???.

### ?? ?? ??? ?? ??

?? scoped SQLite ??? ? read transaction ? DB ??? ????
??? ????. ?? DB? ?? ??? semantic RAM? ?????.
?? ?? ?? ?? 241,031.917ms? ??? ?? ???? ????.
native RAM? activity timestamp ??? ?? ??? ????.
`backup-lock-audit.json`? `ui-registry-backup.json`? ?? ??? ????
?? SQLite ??? ?? ?? ???? ???? ???. Single Vision
??? ??? ? ?? ?? ????. ?? ??? live registry? ?
read lock? ??? ???? ???? ??.

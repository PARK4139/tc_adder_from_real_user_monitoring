# Preferences > General Tab TC

시나리오 작성 초안 · 이슈 `093ca349` · **실행 결과 없음**

트리 경로: **Setup > Preferences > General** · TC ID는 경로와 독립적인 `TC-숫자` 형식으로 관리한다.

작성 규칙 정본: [tc_format.py](../../rules/scenarios/tc_format.py)의 `BODY`.

각 TC는 번호가 있는 **Steps / Expected Result** 묶음으로 구성한다. 하나의 묶음에 여러 동작을 넣고,
묶음의 기대 결과를 확인한 뒤 다음 번호로 진행한다. 같은 TC의 단계들은 상태를 이어받는다.
Steps는 `선택`, `클릭`, `입력`, `확인`, `복원` 등의 동작명으로 끝내며 `한다`, `된다`로 끝내지 않는다.
아래 표는 [Gherkin 초안](preferences_general.feature)의 수행 절차와 기대 결과를 그대로 표시한 결과다.
자동화 구현·실행 등록·Emulator 조작은 수행하지 않았다.

Save 묶음의 “Preferences 창이 열려 있으면 닫기 후 재진입”은 저장 후 이미 닫혔다면 다시 열기만 수행한다.
설정 재진입 검증은 저장값 확인 범위이며 소리·가공·LED 등 실제 기능 효과를 검증했다고 뜻하지 않는다.
모든 기대 결과는 시험 계획이며 실측 결과가 아니다.

## TC 목록

### TC-001 General 화면 진입 및 입력요소 표시

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | General 탭이 선택되어 표시된다<br>Language, Sleep Mode, 숫자 입력 및 라디오 선택 그룹이 표시된다 |
| 2 | 1. General 설정 영역을 위에서 아래까지 스크롤하며 입력요소 확인 | 하기 수집 요소가 각각 보여야 합니다.<br>Backup Date<br>Backup Filename<br>Beep Sound<br>Config DB History<br>Default File Type<br>Digital Designer Mode<br>Easy Click Mode<br>Eccentricity Check<br>Edit Processed Job<br>Export Options<br>Factory Reset Date<br>Fast Processing with Lens Diameter<br>Font<br>Format<br>Frame Fitting Mode<br>Grid<br>Horizontal Space (mm)<br>Language<br>LED Notification<br>Line Ending<br>Message Box Font Size<br>R/L Shape Mirroring<br>Radius Mode<br>Restore Date<br>Restore Filename<br>Safety Check<br>Show Grid<br>Show Tip Message<br>Sleep Mode<br>The Number of Radii(OMA)<br>Vertical Space (mm)<br>Wait (minutes) |
| 3 | 1. General 설정 영역을 맨 위로 스크롤 | Language 입력요소가 다시 표시된다 |

### TC-002 Language 선택 및 저장값 확인 (선택기)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **지원 언어 준비**<br>&nbsp;&nbsp;English 및 승인된 다른 지원 언어 제공 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Language 선택기의 화살표 조작 후 English 선택 | Language에 English가 표시된다 |
| 3 | 1. Language 선택기의 화살표 조작 후 승인된 다른 지원 언어 선택 | Language에 선택한 지원 언어가 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Language에 저장한 지원 언어가 표시된다 |
| 5 | 1. Language를 기록한 원래 언어로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Language가 시험 전 언어로 표시된다 |

### TC-003 Beep Sound 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Beep Sound에서 OFF 항목 선택 | Beep Sound의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Beep Sound에서 ON 항목 선택 | Beep Sound의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Beep Sound의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Beep Sound의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Beep Sound의 선택이 시험 전 값과 일치한다 |

### TC-004 Frame Fitting Mode 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Frame Fitting Mode에서 BOTH 항목 선택 | Frame Fitting Mode의 BOTH 항목이 선택되어 표시된다<br>Right , Left 항목은 선택 해제되어 표시된다 |
| 3 | 1. Frame Fitting Mode에서 Right , Left 항목 선택 | Frame Fitting Mode의 Right , Left 항목이 선택되어 표시된다<br>BOTH 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Frame Fitting Mode의 Right , Left 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Frame Fitting Mode의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Frame Fitting Mode의 선택이 시험 전 값과 일치한다 |

### TC-005 Edit Processed Job 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Edit Processed Job에서 OFF 항목 선택 | Edit Processed Job의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Edit Processed Job에서 ON 항목 선택 | Edit Processed Job의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Edit Processed Job의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Edit Processed Job의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Edit Processed Job의 선택이 시험 전 값과 일치한다 |

### TC-006 Show Tip Message 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Show Tip Message에서 OFF 항목 선택 | Show Tip Message의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Show Tip Message에서 ON 항목 선택 | Show Tip Message의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Show Tip Message의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Show Tip Message의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Show Tip Message의 선택이 시험 전 값과 일치한다 |

### TC-007 Digital Designer Mode 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Digital Designer Mode에서 Digital Pattern 항목 선택 | Digital Designer Mode의 Digital Pattern 항목이 선택되어 표시된다<br>Hole Editor 항목은 선택 해제되어 표시된다 |
| 3 | 1. Digital Designer Mode에서 Hole Editor 항목 선택 | Digital Designer Mode의 Hole Editor 항목이 선택되어 표시된다<br>Digital Pattern 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Digital Designer Mode의 Hole Editor 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Digital Designer Mode의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Digital Designer Mode의 선택이 시험 전 값과 일치한다 |

### TC-008 Show Grid 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Show Grid에서 OFF 항목 선택 | Show Grid의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Show Grid에서 ON 항목 선택 | Show Grid의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Show Grid의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Show Grid의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Show Grid의 선택이 시험 전 값과 일치한다 |

### TC-009 R/L Shape Mirroring 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. R/L Shape Mirroring에서 OFF 항목 선택 | R/L Shape Mirroring의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. R/L Shape Mirroring에서 ON 항목 선택 | R/L Shape Mirroring의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | R/L Shape Mirroring의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. R/L Shape Mirroring의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | R/L Shape Mirroring의 선택이 시험 전 값과 일치한다 |

### TC-010 Eccentricity Check 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Eccentricity Check에서 OFF 항목 선택 | Eccentricity Check의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Eccentricity Check에서 ON 항목 선택 | Eccentricity Check의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Eccentricity Check의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Eccentricity Check의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Eccentricity Check의 선택이 시험 전 값과 일치한다 |

### TC-011 Easy Click Mode 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Easy Click Mode에서 OFF 항목 선택 | Easy Click Mode의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. Easy Click Mode에서 ON 항목 선택 | Easy Click Mode의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Easy Click Mode의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. Easy Click Mode의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Easy Click Mode의 선택이 시험 전 값과 일치한다 |

### TC-012 LED Notification 선택 및 저장값 확인 (라디오 버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. LED Notification에서 OFF 항목 선택 | LED Notification의 OFF 항목이 선택되어 표시된다<br>ON 항목은 선택 해제되어 표시된다 |
| 3 | 1. LED Notification에서 ON 항목 선택 | LED Notification의 ON 항목이 선택되어 표시된다<br>OFF 항목은 선택 해제되어 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | LED Notification의 ON 항목이 저장된 선택으로 표시된다 |
| 5 | 1. LED Notification의 선택을 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | LED Notification의 선택이 시험 전 값과 일치한다 |

### TC-013 Sleep Mode 체크 상태 변경 및 저장값 확인 (체크박스)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Sleep Mode의 체크 해제 | Sleep Mode가 체크 해제 상태로 표시된다 |
| 3 | 1. Sleep Mode 체크 | Sleep Mode가 체크 상태로 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Sleep Mode가 체크 상태로 표시된다 |
| 5 | 1. Sleep Mode를 기록한 원래 체크 상태로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Sleep Mode의 체크 상태가 시험 전 값과 일치한다 |

### TC-014 Wait (minutes) 숫자 입력 및 저장값 확인 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Wait (minutes) 입력 가능, 원래 값과 다른 유효 시험값 승인 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Wait (minutes) 입력요소 선택 | Wait (minutes)의 값을 편집할 수 있는 입력 상태가 표시된다 |
| 3 | 1. Wait (minutes)에 승인된 시험값 입력<br>2. 입력 확정 | Wait (minutes)에 입력한 시험값이 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Wait (minutes)에 저장한 시험값이 표시된다 |
| 5 | 1. Wait (minutes)의 입력값을 기록한 원래 값으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Wait (minutes)의 값이 시험 전 값과 일치한다 |

### TC-015 Wait (minutes) 숫자 입력 경계값 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Wait (minutes) 허용 최솟값·최댓값 확정 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Wait (minutes)에 승인된 최솟값 입력<br>2. 입력 확정 | Wait (minutes)에 승인된 최솟값이 표시된다 |
| 3 | 1. Wait (minutes)에 승인된 최댓값 입력<br>2. 입력 확정 | Wait (minutes)에 승인된 최댓값이 표시된다 |
| 4 | 1. Wait (minutes)의 입력값을 기록한 원래 값으로 복원<br>2. Cancel 클릭 | Preferences 창이 닫힌다 |
| 5 | 1. Preferences를 다시 진입<br>2. General 탭 선택 | Wait (minutes)의 값이 시험 전 값과 일치한다 |

### TC-016 Wait (minutes) 잘못된 숫자 입력 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Wait (minutes) 오류별 입력값·기대 결과 확정 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Wait (minutes)에 빈 값 입력 시도<br>2. 입력 확정 시도 | Wait (minutes)의 빈 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 3 | 1. Wait (minutes)에 비숫자 문자 입력 시도<br>2. 입력 확정 시도 | Wait (minutes)의 비숫자 문자에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 4 | 1. Wait (minutes)에 허용 범위 미만 값 입력 시도<br>2. 입력 확정 시도 | Wait (minutes)의 허용 범위 미만 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 5 | 1. Wait (minutes)에 허용 범위 초과 값 입력 시도<br>2. 입력 확정 시도 | Wait (minutes)의 허용 범위 초과 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 6 | 1. Wait (minutes)의 입력값을 기록한 원래 값으로 복원<br>2. Cancel 클릭 | Preferences 창이 닫힌다 |
| 7 | 1. Preferences를 다시 진입<br>2. General 탭 선택 | Wait (minutes)의 값이 시험 전 값과 일치한다 |

### TC-017 Message Box Font Size 숫자 입력 및 저장값 확인 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Message Box Font Size 입력 가능, 원래 값과 다른 유효 시험값 승인 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Message Box Font Size 입력요소 선택 | Message Box Font Size의 값을 편집할 수 있는 입력 상태가 표시된다 |
| 3 | 1. Message Box Font Size에 승인된 시험값 입력<br>2. 입력 확정 | Message Box Font Size에 입력한 시험값이 표시된다 |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Message Box Font Size에 저장한 시험값이 표시된다 |
| 5 | 1. Message Box Font Size의 입력값을 기록한 원래 값으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Message Box Font Size의 값이 시험 전 값과 일치한다 |

### TC-018 Message Box Font Size 숫자 입력 경계값 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Message Box Font Size 허용 최솟값·최댓값 확정 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Message Box Font Size에 승인된 최솟값 입력<br>2. 입력 확정 | Message Box Font Size에 승인된 최솟값이 표시된다 |
| 3 | 1. Message Box Font Size에 승인된 최댓값 입력<br>2. 입력 확정 | Message Box Font Size에 승인된 최댓값이 표시된다 |
| 4 | 1. Message Box Font Size의 입력값을 기록한 원래 값으로 복원<br>2. Cancel 클릭 | Preferences 창이 닫힌다 |
| 5 | 1. Preferences를 다시 진입<br>2. General 탭 선택 | Message Box Font Size의 값이 시험 전 값과 일치한다 |

### TC-019 Message Box Font Size 잘못된 숫자 입력 (숫자 입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |
| 2 | **시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;Message Box Font Size 오류별 입력값·기대 결과 확정 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Message Box Font Size에 빈 값 입력 시도<br>2. 입력 확정 시도 | Message Box Font Size의 빈 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 3 | 1. Message Box Font Size에 비숫자 문자 입력 시도<br>2. 입력 확정 시도 | Message Box Font Size의 비숫자 문자에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 4 | 1. Message Box Font Size에 허용 범위 미만 값 입력 시도<br>2. 입력 확정 시도 | Message Box Font Size의 허용 범위 미만 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 5 | 1. Message Box Font Size에 허용 범위 초과 값 입력 시도<br>2. 입력 확정 시도 | Message Box Font Size의 허용 범위 초과 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다 |
| 6 | 1. Message Box Font Size의 입력값을 기록한 원래 값으로 복원<br>2. Cancel 클릭 | Preferences 창이 닫힌다 |
| 7 | 1. Preferences를 다시 진입<br>2. General 탭 선택 | Message Box Font Size의 값이 시험 전 값과 일치한다 |

### TC-030 Config DB History 입력 및 저장값 확인 (입력란)

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;Config DB History의 원래 값 기록<br>&nbsp;&nbsp;시험 후 복구 방법 기록 |
| 2 | **Config DB History 시험값 및 처리 규칙 준비**<br>&nbsp;&nbsp;입력 가능 여부와 실제 입력유형 확인 후 확정<br>&nbsp;&nbsp;허용 형식 및 범위와 저장 후 재표시 규칙 확인 후 확정<br>&nbsp;&nbsp;시험값: 시험 전 값과 다른 승인된 유효 값으로 확정 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. General 설정 영역에서 Config DB History 항목까지 스크롤 | Config DB History 항목과 입력란이 표시된다 |
| 3 | 1. Config DB History 입력란 선택 | Config DB History 값을 편집할 수 있는 입력 상태가 표시된다 |
| 4 | 1. Config DB History에 승인된 시험값 입력<br>2. 입력 확정 | Config DB History 입력란에 입력한 시험값이 표시된다 |
| 5 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택<br>4. General 설정 영역에서 Config DB History 항목까지 스크롤 | Config DB History 입력란에 저장한 시험값이 표시된다 |
| 6 | 1. Config DB History 입력값을 기록한 원래 값으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택<br>5. General 설정 영역에서 Config DB History 항목까지 스크롤 | Config DB History 값이 시험 전 값과 일치한다 |

### TC-040 Export Options 항목 표시 및 접근 확인

**작성 상태:** 입력값 또는 처리 규칙 확정 필요

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **Export Options 위치 및 입력요소 확인 준비**<br>&nbsp;&nbsp;General 탭의 Export Options 실제 표시 위치 확인<br>&nbsp;&nbsp;입력유형과 선택값 및 클릭 후 화면 동작 확인 후 확정<br>&nbsp;&nbsp;저장과 취소 동작 확인 후 해당 입력유형 TC 추가 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. General 설정 영역에서 Export Options 항목까지 스크롤 | Export Options 항목이 표시된다 |

### TC-020 Save 버튼의 설정 저장 (버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Beep Sound에서 시험 전 값과 다른 선택지 선택 | Beep Sound에 변경한 선택지가 선택 상태로 표시된다 |
| 3 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | Beep Sound에 변경한 선택지가 저장되어 표시된다 |
| 4 | 1. Beep Sound를 기록한 원래 선택으로 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | Beep Sound의 선택이 시험 전 값과 일치한다 |

### TC-021 Cancel 버튼의 설정 변경 취소 (버튼)

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. Beep Sound에서 시험 전 값과 다른 선택지 선택 | Beep Sound에 변경한 선택지가 선택 상태로 표시된다 |
| 3 | 1. Cancel 클릭 | Preferences 창이 닫힌다 |
| 4 | 1. Preferences를 다시 진입<br>2. General 탭 선택 | Beep Sound의 선택이 시험 전 값과 일치한다 |

### TC-022 General 스크롤 및 설정값 유지

**작성 상태:** 시나리오 초안

**사전 조건**

| Step | Steps |
|---|---|
| 1 | **설정값 복구 준비**<br>&nbsp;&nbsp;원래 설정값과 복구 방법 기록 |

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 표시된다 |
| 2 | 1. General 설정 영역을 맨 위로 스크롤 | Language 입력요소가 표시된다 |
| 3 | 1. General 설정 영역을 아래로 스크롤 | 아래쪽 설정 영역이 표시된다<br>General 탭은 선택 상태를 유지한다 |
| 4 | 1. General 설정 영역을 맨 위로 스크롤 | Language 입력요소가 다시 표시된다<br>설정값이 시험 전 값과 일치한다 |

## 근거와 미확정 사항

- Export Options는 사용자 누락 지적으로 표시·접근 TC 초안을 추가했다. 실제 위치·입력유형·선택값·저장·취소 동작은 첫 수집 이미지에서 확인되지 않아 해당 유형의 동작 TC는 추가 확인이 필요하다.

- Config DB History 입력란은 사용자 확인으로 추가했다. 첫 수집 이미지에 해당 항목이 표시되지 않아 실제 입력유형·허용 값·저장 동작은 확인 필요다. 입력란 TC 초안이며 실행 결과는 없다.

- 기존 수집: `{D_TEMP}/hpe990/evidence/ui/6ae4034bdc184ce29b7c200d12230ad5/ba6c8e1a2fad4d66be88414dfc42f73a/inventory.json` 및 Preferences 이미지 `1835796.png`.
- Language는 이미지에서 위·아래 화살표 선택기로 관찰했다. 사용자 양식 예시의 Language 드롭다운 동작을 이 제품에 그대로 가정하지 않았다. 전체 언어 목록과 실제 선택 방식은 확인이 필요하다.
- 숫자 입력의 편집 방식·허용 범위·유효 변경값·오류별 단일 기대 결과는 미확정이다. 이미지의 30분과 글꼴 크기16은 표시값이지 입력·저장 성공 증거가 아니다.
- 숫자 및 언어의 확인 필요 TC는 검토용 골격이다. 미확정 문구를 실제 입력값과 구체적인 표시 결과로 바꾸기 전에는 실행용 TC로 사용하지 않는다.
- Save 이후 창 닫힘·유지 방식, Cancel의 실제 취소 동작은 실행 검증하지 않았다.
- Sleep Mode와 Wait의 활성 상태 연동 및 스크롤 아래 미관찰 요소는 미확인이다. General 전체 UI를 빠짐없이 작성했다는 주장은 하지 않는다.
- 초안은 `docs/bdd/`에 보관하며, 바인딩 완료 전에는 `tests/bdd/scenarios/features/` 및 실행 등록 목록에 추가하지 않는다.

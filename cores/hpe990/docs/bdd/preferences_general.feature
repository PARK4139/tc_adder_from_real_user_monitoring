@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-001 @type-navigation @expected-collected-General
  Scenario: TC-001 General 화면 진입 및 입력요소 표시
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then General 탭이 선택되어 표시된다
    And Language, Sleep Mode, 숫자 입력 및 라디오 선택 그룹이 표시된다
    # Step 2
    When General 설정 영역을 위에서 아래까지 스크롤하며 입력요소 확인
    # BEGIN collected General elements
    Then 하기 수집 요소가 각각 보여야 합니다.
    # UI reference: UI-000111
    And Backup Date
    # UI reference: UI-000108
    And Backup Filename
    # UI reference: UI-000089
    And Beep Sound
    # UI reference: UI-000093
    And Config DB History
    # UI reference: UI-000029
    And Default File Type
    # UI reference: UI-000069
    And Digital Designer Mode
    # UI reference: UI-000049
    And Easy Click Mode
    # UI reference: UI-000054
    And Eccentricity Check
    # UI reference: UI-000077
    And Edit Processed Job
    # UI reference: UI-000024
    And Export Options
    # UI reference: UI-000095
    And Factory Reset Date
    # UI reference: UI-000037
    And Fast Processing with Lens Diameter
    # UI reference: UI-000045
    And Font
    # UI reference: UI-000025
    And Format
    # UI reference: UI-000085
    And Frame Fitting Mode
    # UI reference: UI-000062
    And Grid
    # UI reference: UI-000064
    And Horizontal Space (mm)
    # UI reference: UI-000114
    And Language
    # UI reference: UI-000041
    And LED Notification
    # UI reference: UI-000031
    And Line Ending
    # UI reference: UI-000047
    And Message Box Font Size
    # UI reference: UI-000058
    And R/L Shape Mirroring
    # UI reference: UI-000026
    And Radius Mode
    # UI reference: UI-000103
    And Restore Date
    # UI reference: UI-000100
    And Restore Filename
    # UI reference: UI-000053
    And Safety Check
    # UI reference: UI-000065
    And Show Grid
    # UI reference: UI-000073
    And Show Tip Message
    # UI reference: UI-000081
    And Sleep Mode
    # UI reference: UI-000027
    And The Number of Radii(OMA)
    # UI reference: UI-000063
    And Vertical Space (mm)
    # UI reference: UI-000083
    And Wait (minutes)
    # END collected General elements
    # Step 3
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 다시 표시된다

  @TC-002 @type-option-selector @requires-specification @spec-language-options
  Scenario: TC-002 Language 선택 및 저장값 확인 (선택기)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 지원 언어 준비
      """
      English 및 승인된 다른 지원 언어 제공
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Language 선택기의 화살표 조작 후 English 선택
    Then Language에 English가 표시된다
    # Step 3
    When Language 선택기의 화살표 조작 후 승인된 다른 지원 언어 선택
    Then Language에 선택한 지원 언어가 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Language에 저장한 지원 언어가 표시된다
    # Step 5
    When Language를 기록한 원래 언어로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Language가 시험 전 언어로 표시된다

  @TC-003 @type-radio
  Scenario: TC-003 Beep Sound 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Beep Sound에서 OFF 항목 선택
    Then Beep Sound의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Beep Sound에서 ON 항목 선택
    Then Beep Sound의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Beep Sound의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Beep Sound의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Beep Sound의 선택이 시험 전 값과 일치한다

  @TC-004 @type-radio
  Scenario: TC-004 Frame Fitting Mode 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Frame Fitting Mode에서 BOTH 항목 선택
    Then Frame Fitting Mode의 BOTH 항목이 선택되어 표시된다
    And Right , Left 항목은 선택 해제되어 표시된다
    # Step 3
    When Frame Fitting Mode에서 Right , Left 항목 선택
    Then Frame Fitting Mode의 Right , Left 항목이 선택되어 표시된다
    And BOTH 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Frame Fitting Mode의 Right , Left 항목이 저장된 선택으로 표시된다
    # Step 5
    When Frame Fitting Mode의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Frame Fitting Mode의 선택이 시험 전 값과 일치한다

  @TC-005 @type-radio
  Scenario: TC-005 Edit Processed Job 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Edit Processed Job에서 OFF 항목 선택
    Then Edit Processed Job의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Edit Processed Job에서 ON 항목 선택
    Then Edit Processed Job의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Edit Processed Job의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Edit Processed Job의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Edit Processed Job의 선택이 시험 전 값과 일치한다

  @TC-006 @type-radio
  Scenario: TC-006 Show Tip Message 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Show Tip Message에서 OFF 항목 선택
    Then Show Tip Message의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Show Tip Message에서 ON 항목 선택
    Then Show Tip Message의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Show Tip Message의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Show Tip Message의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Show Tip Message의 선택이 시험 전 값과 일치한다

  @TC-007 @type-radio
  Scenario: TC-007 Digital Designer Mode 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Digital Designer Mode에서 Digital Pattern 항목 선택
    Then Digital Designer Mode의 Digital Pattern 항목이 선택되어 표시된다
    And Hole Editor 항목은 선택 해제되어 표시된다
    # Step 3
    When Digital Designer Mode에서 Hole Editor 항목 선택
    Then Digital Designer Mode의 Hole Editor 항목이 선택되어 표시된다
    And Digital Pattern 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Digital Designer Mode의 Hole Editor 항목이 저장된 선택으로 표시된다
    # Step 5
    When Digital Designer Mode의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Digital Designer Mode의 선택이 시험 전 값과 일치한다

  @TC-008 @type-radio
  Scenario: TC-008 Show Grid 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Show Grid에서 OFF 항목 선택
    Then Show Grid의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Show Grid에서 ON 항목 선택
    Then Show Grid의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Show Grid의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Show Grid의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Show Grid의 선택이 시험 전 값과 일치한다

  @TC-009 @type-radio
  Scenario: TC-009 R/L Shape Mirroring 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When R/L Shape Mirroring에서 OFF 항목 선택
    Then R/L Shape Mirroring의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When R/L Shape Mirroring에서 ON 항목 선택
    Then R/L Shape Mirroring의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then R/L Shape Mirroring의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When R/L Shape Mirroring의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then R/L Shape Mirroring의 선택이 시험 전 값과 일치한다

  @TC-010 @type-radio
  Scenario: TC-010 Eccentricity Check 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Eccentricity Check에서 OFF 항목 선택
    Then Eccentricity Check의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Eccentricity Check에서 ON 항목 선택
    Then Eccentricity Check의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Eccentricity Check의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Eccentricity Check의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Eccentricity Check의 선택이 시험 전 값과 일치한다

  @TC-011 @type-radio
  Scenario: TC-011 Easy Click Mode 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Easy Click Mode에서 OFF 항목 선택
    Then Easy Click Mode의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When Easy Click Mode에서 ON 항목 선택
    Then Easy Click Mode의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Easy Click Mode의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When Easy Click Mode의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Easy Click Mode의 선택이 시험 전 값과 일치한다

  @TC-012 @type-radio
  Scenario: TC-012 LED Notification 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When LED Notification에서 OFF 항목 선택
    Then LED Notification의 OFF 항목이 선택되어 표시된다
    And ON 항목은 선택 해제되어 표시된다
    # Step 3
    When LED Notification에서 ON 항목 선택
    Then LED Notification의 ON 항목이 선택되어 표시된다
    And OFF 항목은 선택 해제되어 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then LED Notification의 ON 항목이 저장된 선택으로 표시된다
    # Step 5
    When LED Notification의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then LED Notification의 선택이 시험 전 값과 일치한다

  @TC-013 @type-checkbox
  Scenario: TC-013 Sleep Mode 체크 상태 변경 및 저장값 확인 (체크박스)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Sleep Mode의 체크 해제
    Then Sleep Mode가 체크 해제 상태로 표시된다
    # Step 3
    When Sleep Mode 체크
    Then Sleep Mode가 체크 상태로 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Sleep Mode가 체크 상태로 표시된다
    # Step 5
    When Sleep Mode를 기록한 원래 체크 상태로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Sleep Mode의 체크 상태가 시험 전 값과 일치한다

  @TC-014 @type-number @requires-specification @spec-test-value
  Scenario: TC-014 Wait (minutes) 숫자 입력 및 저장값 확인 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Wait (minutes) 입력 가능, 원래 값과 다른 유효 시험값 승인
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Wait (minutes) 입력요소 선택
    Then Wait (minutes)의 값을 편집할 수 있는 입력 상태가 표시된다
    # Step 3
    When Wait (minutes)에 승인된 시험값 입력
    And 입력 확정
    Then Wait (minutes)에 입력한 시험값이 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Wait (minutes)에 저장한 시험값이 표시된다
    # Step 5
    When Wait (minutes)의 입력값을 기록한 원래 값으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Wait (minutes)의 값이 시험 전 값과 일치한다

  @TC-015 @type-number @requires-specification @spec-number-range
  Scenario: TC-015 Wait (minutes) 숫자 입력 경계값 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Wait (minutes) 허용 최솟값·최댓값 확정
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Wait (minutes)에 승인된 최솟값 입력
    And 입력 확정
    Then Wait (minutes)에 승인된 최솟값이 표시된다
    # Step 3
    When Wait (minutes)에 승인된 최댓값 입력
    And 입력 확정
    Then Wait (minutes)에 승인된 최댓값이 표시된다
    # Step 4
    When Wait (minutes)의 입력값을 기록한 원래 값으로 복원
    And Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 5
    When Preferences를 다시 진입
    And General 탭 선택
    Then Wait (minutes)의 값이 시험 전 값과 일치한다

  @TC-016 @type-number @requires-specification @spec-error-handling
  Scenario: TC-016 Wait (minutes) 잘못된 숫자 입력 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Wait (minutes) 오류별 입력값·기대 결과 확정
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Wait (minutes)에 빈 값 입력 시도
    And 입력 확정 시도
    Then Wait (minutes)의 빈 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 3
    When Wait (minutes)에 비숫자 문자 입력 시도
    And 입력 확정 시도
    Then Wait (minutes)의 비숫자 문자에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 4
    When Wait (minutes)에 허용 범위 미만 값 입력 시도
    And 입력 확정 시도
    Then Wait (minutes)의 허용 범위 미만 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 5
    When Wait (minutes)에 허용 범위 초과 값 입력 시도
    And 입력 확정 시도
    Then Wait (minutes)의 허용 범위 초과 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 6
    When Wait (minutes)의 입력값을 기록한 원래 값으로 복원
    And Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 7
    When Preferences를 다시 진입
    And General 탭 선택
    Then Wait (minutes)의 값이 시험 전 값과 일치한다

  @TC-017 @type-number @requires-specification @spec-test-value
  Scenario: TC-017 Message Box Font Size 숫자 입력 및 저장값 확인 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Message Box Font Size 입력 가능, 원래 값과 다른 유효 시험값 승인
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Message Box Font Size 입력요소 선택
    Then Message Box Font Size의 값을 편집할 수 있는 입력 상태가 표시된다
    # Step 3
    When Message Box Font Size에 승인된 시험값 입력
    And 입력 확정
    Then Message Box Font Size에 입력한 시험값이 표시된다
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Message Box Font Size에 저장한 시험값이 표시된다
    # Step 5
    When Message Box Font Size의 입력값을 기록한 원래 값으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Message Box Font Size의 값이 시험 전 값과 일치한다

  @TC-018 @type-number @requires-specification @spec-number-range
  Scenario: TC-018 Message Box Font Size 숫자 입력 경계값 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Message Box Font Size 허용 최솟값·최댓값 확정
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Message Box Font Size에 승인된 최솟값 입력
    And 입력 확정
    Then Message Box Font Size에 승인된 최솟값이 표시된다
    # Step 3
    When Message Box Font Size에 승인된 최댓값 입력
    And 입력 확정
    Then Message Box Font Size에 승인된 최댓값이 표시된다
    # Step 4
    When Message Box Font Size의 입력값을 기록한 원래 값으로 복원
    And Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 5
    When Preferences를 다시 진입
    And General 탭 선택
    Then Message Box Font Size의 값이 시험 전 값과 일치한다

  @TC-019 @type-number @requires-specification @spec-error-handling
  Scenario: TC-019 Message Box Font Size 잘못된 숫자 입력 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    And 시험값 및 처리 규칙 준비
      """
      Message Box Font Size 오류별 입력값·기대 결과 확정
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Message Box Font Size에 빈 값 입력 시도
    And 입력 확정 시도
    Then Message Box Font Size의 빈 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 3
    When Message Box Font Size에 비숫자 문자 입력 시도
    And 입력 확정 시도
    Then Message Box Font Size의 비숫자 문자에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 4
    When Message Box Font Size에 허용 범위 미만 값 입력 시도
    And 입력 확정 시도
    Then Message Box Font Size의 허용 범위 미만 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 5
    When Message Box Font Size에 허용 범위 초과 값 입력 시도
    And 입력 확정 시도
    Then Message Box Font Size의 허용 범위 초과 값에 대해 확정된 처리 규칙과 일치하는 결과가 표시된다
    # Step 6
    When Message Box Font Size의 입력값을 기록한 원래 값으로 복원
    And Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 7
    When Preferences를 다시 진입
    And General 탭 선택
    Then Message Box Font Size의 값이 시험 전 값과 일치한다

  @TC-030 @type-input-field @requires-specification @spec-input-type @spec-input-format @spec-save-display
  Scenario: TC-030 Config DB History 입력 및 저장값 확인 (입력란)
    Given 설정값 복구 준비
      """
      Config DB History의 원래 값 기록
      시험 후 복구 방법 기록
      """
    And Config DB History 시험값 및 처리 규칙 준비
      """
      입력 가능 여부와 실제 입력유형 확인 후 확정
      허용 형식 및 범위와 저장 후 재표시 규칙 확인 후 확정
        시험값: 시험 전 값과 다른 승인된 유효 값으로 확정
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 항목과 입력란이 표시된다
    # Step 3
    When Config DB History 입력란 선택
    Then Config DB History 값을 편집할 수 있는 입력 상태가 표시된다
    # Step 4
    When Config DB History에 승인된 시험값 입력
    And 입력 확정
    Then Config DB History 입력란에 입력한 시험값이 표시된다
    # Step 5
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    And General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 입력란에 저장한 시험값이 표시된다
    # Step 6
    When Config DB History 입력값을 기록한 원래 값으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    And General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 값이 시험 전 값과 일치한다

  @TC-040 @type-navigation @requires-specification @spec-input-type @spec-option-values @spec-click-behavior
  Scenario: TC-040 Export Options 항목 표시 및 접근 확인
    Given Export Options 위치 및 입력요소 확인 준비
      """
      General 탭의 Export Options 실제 표시 위치 확인
      입력유형과 선택값 및 클릭 후 화면 동작 확인 후 확정
      저장과 취소 동작 확인 후 해당 입력유형 TC 추가
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When General 설정 영역에서 Export Options 항목까지 스크롤
    Then Export Options 항목이 표시된다

  @TC-020 @type-button
  Scenario: TC-020 Save 버튼의 설정 저장 (버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Beep Sound에서 시험 전 값과 다른 선택지 선택
    Then Beep Sound에 변경한 선택지가 선택 상태로 표시된다
    # Step 3
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Beep Sound에 변경한 선택지가 저장되어 표시된다
    # Step 4
    When Beep Sound를 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Beep Sound의 선택이 시험 전 값과 일치한다

  @TC-021 @type-button
  Scenario: TC-021 Cancel 버튼의 설정 변경 취소 (버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When Beep Sound에서 시험 전 값과 다른 선택지 선택
    Then Beep Sound에 변경한 선택지가 선택 상태로 표시된다
    # Step 3
    When Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 4
    When Preferences를 다시 진입
    And General 탭 선택
    Then Beep Sound의 선택이 시험 전 값과 일치한다

  @TC-022 @type-scroll
  Scenario: TC-022 General 스크롤 및 설정값 유지
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 표시된다
    # Step 2
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 표시된다
    # Step 3
    When General 설정 영역을 아래로 스크롤
    Then 아래쪽 설정 영역이 표시된다
    And General 탭은 선택 상태를 유지한다
    # Step 4
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 다시 표시된다
    And 설정값이 시험 전 값과 일치한다

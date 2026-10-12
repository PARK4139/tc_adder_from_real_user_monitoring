@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-010 @type-navigation @expected-collected-General
  Scenario: TC-010 General 화면 진입 및 입력요소 표시
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then General 탭이 선택되어 보여야 합니다.
    And Language, Sleep Mode, 숫자 입력 및 라디오 선택 그룹이 보여야 합니다.
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
    # UI reference: UI-002263
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
    # UI reference: UI-002266
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
    # UI reference: UI-002269
    And The Number of Radii(OMA)
    # UI reference: UI-000063
    And Vertical Space (mm)
    # UI reference: UI-000083
    And Wait (minutes)
    # END collected General elements
    # Step 3
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 다시 보여야 합니다.

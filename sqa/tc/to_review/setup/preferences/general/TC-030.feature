@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  # 관찰 기반: English/Korean 간 설정 및 적용 확인. 제품 사양 일치 또는 모든 화면 번역 보장은 아님.
  # MCP/Real Activity Monitoring 증거: {D_TEMP}/hpe990/evidence/093ca349/language-live/report.md
  # UI semantic reference: HPE990.Setup.Preferences.General.Language
  @TC-030 @observed-behavior @type-option-selector
  Scenario: TC-030 Language 설정 및 적용 확인 (선택기)
    Given Edger 화면에서 Setup 버튼 클릭
    And Setup > Preferences > General 탭 선택
    And Language의 시험 전 값 English 확인
    # Step 1
    When Language 클릭
    Then 언어 목록 팝업이 펼쳐져 보여야 합니다.
    And English, Korean, Russian, French, German, Japanese, Chinese, Polish, Spanish, Italian, Bulgarian, Portuguese 항목이 보여야 합니다.
    # Step 2
    When Korean 선택
    Then Language에 Korean이 보여야 합니다.
    And 언어 목록 팝업이 닫혀야 합니다.
    # Step 3
    When Save 클릭
    Then Preferences 창이 닫혀야 합니다.
    And Setup 화면 제목에 메뉴가 보여야 합니다.
    And 메뉴 화면에 환경 설정, 시간 설정, 터치스크린 검사 항목이 보여야 합니다.
    # Step 4
    When 메뉴 > 환경 설정 > 일반 탭 선택
    Then 언어 항목에 한국어가 유지되어 보여야 합니다.
    And 환경 설정 화면에 일반, 언어, 저장, 취소 문구가 보여야 합니다.
    # Step 5
    When 언어 클릭 후 영어 선택
    And 저장 클릭
    Then 환경 설정 창이 닫혀야 합니다.
    And 메뉴 화면 제목에 Setup이 보여야 합니다.
    And Preferences, Date & Time, Touch Test 항목이 보여야 합니다.
    # Step 6
    When Setup > Preferences > General 탭 선택
    Then Language에 시험 전 값인 English가 유지되어 보여야 합니다.
    And Preferences 화면에 General, Language, Save, Cancel 문구가 보여야 합니다.

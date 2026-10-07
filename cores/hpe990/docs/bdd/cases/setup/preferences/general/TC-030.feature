@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-030 @actual-behavior-check @type-option-selector @requires-specification @spec-language-options
  Scenario: TC-030 Language 선택 및 저장값 확인 (선택기)
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
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When Language 선택기의 화살표 조작 후 English 선택
    Then Language에 English가 보여야 합니다.
    # Step 3
    When Language 선택기의 화살표 조작 후 승인된 다른 지원 언어 선택
    Then Language에 선택한 지원 언어가 보여야 합니다.
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Language에 저장한 지원 언어가 보여야 합니다.
    # Step 5
    When Language를 기록한 원래 언어로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Language가 시험 전 언어로 보여야 합니다.

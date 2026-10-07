@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-150 @actual-behavior-check @type-radio
  Scenario: TC-150 Eccentricity Check 선택 및 저장값 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When Eccentricity Check에서 OFF 항목 선택
    Then Eccentricity Check의 OFF 항목이 선택되어 보여야 합니다.
    And ON 항목은 선택 해제되어 보여야 합니다.
    # Step 3
    When Eccentricity Check에서 ON 항목 선택
    Then Eccentricity Check의 ON 항목이 선택되어 보여야 합니다.
    And OFF 항목은 선택 해제되어 보여야 합니다.
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Eccentricity Check의 ON 항목이 저장된 선택으로 보여야 합니다.
    # Step 5
    When Eccentricity Check의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Eccentricity Check의 선택이 시험 전 값과 일치한다

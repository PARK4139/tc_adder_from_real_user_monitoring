@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-020 @type-scroll
  Scenario: TC-020 General 스크롤 및 설정값 유지
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 보여야 합니다.
    # Step 3
    When General 설정 영역을 아래로 스크롤
    Then 아래쪽 설정 영역이 보여야 합니다.
    And General 탭은 선택 상태를 유지한다
    # Step 4
    When General 설정 영역을 맨 위로 스크롤
    Then Language 입력요소가 다시 보여야 합니다.
    And 설정값이 시험 전 값과 일치한다

@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-200 @actual-behavior-check @type-radio @requires-specification
  Scenario: TC-200 LED Notification 설정 및 적용 확인 (라디오 버튼)
    Given 설정값 복구 준비
      """
      LED Notification의 원래 선택값과 복구 방법 기록
      """
    And LED 알림 적용 확인 준비
      """
      ON/OFF에서 동일하게 실행할 알림 발생 조건 확인 후 확정
      LED 관찰 대상 및 관찰 방법 확인 후 확정
      사양 근거와 실동작 증거 미확보 상태에서는 적용 확인을 PASS로 판정하지 않음
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When LED Notification에서 ON 항목 선택
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then LED Notification의 ON 항목이 저장된 선택으로 보여야 합니다.
    And OFF 항목은 선택 해제되어 보여야 합니다.
    # Step 3
    When 설정 화면 종료 후 확정된 LED 알림 발생 조건 실행
    And 준비한 관찰 방법으로 LED 알림 확인
    Then LED 알림이 보여져야한다.(**사양근거 기반 실동작확인필요**)
    # Step 4
    When Setup > Preferences > General 탭 선택
    And LED Notification에서 OFF 항목 선택
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then LED Notification의 OFF 항목이 저장된 선택으로 보여야 합니다.
    And ON 항목은 선택 해제되어 보여야 합니다.
    # Step 5
    When 설정 화면 종료 후 ON 시험과 동일한 LED 알림 발생 조건 실행
    And 준비한 관찰 방법으로 LED 알림 확인
    Then 해당 LED 알림이 발생하지 않아야 한다.(**사양근거 기반 실동작확인필요**)
    # Step 6
    When Setup > Preferences > General 탭 선택
    And LED Notification의 선택을 기록한 원래 선택으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then LED Notification의 선택이 시험 전 값과 일치해야 합니다.

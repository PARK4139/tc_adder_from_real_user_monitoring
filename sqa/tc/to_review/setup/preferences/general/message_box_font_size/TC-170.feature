@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General/Message%20Box%20Font%20Size
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-170 @actual-behavior-check @type-number @requires-specification @spec-test-value
  Scenario: TC-170 Message Box Font Size 숫자 입력 및 저장값 확인 (숫자 입력란)
    Given 설정값 복구 준비
      """
      원래 설정값과 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When Message Box Font Size 입력요소 선택
    Then Message Box Font Size의 값을 편집할 수 있는 입력 상태가 보여야 합니다.
    # Step 3
    When Message Box Font Size에 승인된 시험값 입력
    And 입력 확정
    Then Message Box Font Size에 입력한 시험값이 보여야 합니다.
    # Step 4
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Message Box Font Size에 저장한 시험값이 보여야 합니다.
    # Step 5
    When Message Box Font Size의 입력값을 기록한 원래 값으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    Then Message Box Font Size의 값이 시험 전 값과 일치한다

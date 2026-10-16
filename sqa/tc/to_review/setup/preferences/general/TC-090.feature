@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-090 @type-number @requires-specification @spec-error-handling
  Scenario: TC-090 Sleep Mode / Wait (minutes) 잘못된 숫자 입력 (숫자 입력란)
    # 실행 전 확인 필요: 허용 입력 범위와 각 잘못된 입력의 단일 기대 결과 확정.
    Given Edger 화면에서 Setup 버튼 클릭
    And Setup > Preferences > General 탭 선택
    And Wait (minutes)의 시험 전 값 확인
    # Step 1
    When Wait (minutes)에 빈 값 입력 시도
    And 입력 확정 시도
    Then 빈 값 입력 후 표시되어야 하는 검증 결과는 사양 확인 필요입니다.
    # Step 2
    When Wait (minutes)에 비숫자 문자 입력 시도
    And 입력 확정 시도
    Then 비숫자 입력 후 표시되어야 하는 검증 결과는 사양 확인 필요입니다.
    # Step 3
    When Wait (minutes)에 허용 범위 미만 값 입력 시도
    And 입력 확정 시도
    Then 허용 범위 미만 입력 후 표시되어야 하는 검증 결과는 사양 확인 필요입니다.
    # Step 4
    When Wait (minutes)에 허용 범위 초과 값 입력 시도
    And 입력 확정 시도
    Then 허용 범위 초과 입력 후 표시되어야 하는 검증 결과는 사양 확인 필요입니다.
    # Step 5
    When Wait (minutes)의 입력값을 기록한 원래 값으로 복원
    And Cancel 클릭
    Then Preferences 창이 닫힌다
    # Step 6
    When Preferences를 다시 진입
    And General 탭 선택
    Then Wait (minutes)의 값이 시험 전 값과 일치한다

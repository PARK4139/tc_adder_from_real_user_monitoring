@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Edger/Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-210 @actual-behavior-check @type-input-field @requires-specification @spec-input-type @spec-input-format @spec-save-display
  Scenario: TC-210 Config DB History 입력 및 저장값 확인 (입력란)
    Given 설정값 복구 준비
      """
      Config DB History의 원래 값 기록
      시험 후 복구 방법 기록
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 항목과 입력란이 보여야 합니다.
    # Step 3
    When Config DB History 입력란 선택
    Then Config DB History 값을 편집할 수 있는 입력 상태가 보여야 합니다.
    # Step 4
    When Config DB History에 승인된 시험값 입력
    And 입력 확정
    Then Config DB History 입력란에 입력한 시험값이 보여야 합니다.
    # Step 5
    When Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    And General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 입력란에 저장한 시험값이 보여야 합니다.
    # Step 6
    When Config DB History 입력값을 기록한 원래 값으로 복원
    And Save 클릭
    And Preferences 창이 열려 있으면 닫기 후 재진입
    And General 탭 선택
    And General 설정 영역에서 Config DB History 항목까지 스크롤
    Then Config DB History 값이 시험 전 값과 일치한다

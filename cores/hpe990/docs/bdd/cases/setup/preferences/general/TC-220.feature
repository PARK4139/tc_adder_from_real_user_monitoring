@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: Preferences > General 번호별 Steps / Expected Result TC
  각 Scenario는 하나의 TC이고 번호별 Step 묶음의 상태를 다음 묶음이 이어받는다.
  When과 이어지는 And는 수행 절차이며 Then과 이어지는 And는 해당 묶음의 기대 결과다.
  이 파일은 시나리오 초안으로 자동화 구현 및 실행 등록은 포함하지 않는다.

  @TC-220 @type-navigation @requires-specification @spec-input-type @spec-option-values @spec-click-behavior
  Scenario: TC-220 Export Options 항목 표시 및 접근 확인
    Given Export Options 위치 및 입력요소 확인 준비
      """
      General 탭의 Export Options 실제 표시 위치 확인
      입력유형과 선택값 및 클릭 후 화면 동작 확인 후 확정
      저장과 취소 동작 확인 후 해당 입력유형 TC 추가
      """
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then Preferences 창의 General 탭과 설정 영역이 보여야 합니다.
    # Step 2
    When General 설정 영역에서 Export Options 항목까지 스크롤
    Then Export Options 항목이 보여야 합니다.

@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/작업%20불러오기
Feature: Edger 작업 불러오기 검수 TC

  # MCP/RAM 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-250 @observed-behavior @type-navigation
  Scenario: TC-250 작업 미선택 상태의 UI 확인
    Given Emulator 초기 화면 준비
      """
      시험용 HPE990 Emulator의 새 시험 세션 준비
      실행 대상: C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Huvitz_pc\HPE990\HPE990.lnk
      Continue 클릭 후 작업을 불러오지 않은 Edger 화면 준비
      """
    And 관찰 조건 준비
      """
      관찰 기준: HPE990 GUI 1.22.0, Language English
      시험 중 화면 변화와 수행 시각 기록
      """
    # Step 1
    When Edger의 작업 번호 영역 및 도형 영역 확인
    Then Edger 화면이 보여야 합니다.
    And 작업 번호 영역에 불러온 작업 번호가 없는 상태로 보여야 합니다.
    And 도형 영역에 작업 도형이 없는 상태로 보여야 합니다.
    # Step 2
    When Edger 하단의 Job Editor 아이콘 및 옵션 영역 확인
    Then Job Editor 아이콘과 작업 옵션 영역이 회색 상태로 보여야 합니다.


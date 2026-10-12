@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/작업%20불러오기
Feature: Edger 작업 불러오기 검수 TC

  # MCP/RAM 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-280 @observed-behavior @type-navigation
  Scenario: TC-280 작업 불러오기 후 주요 UI 활성화 확인
    Given Emulator 및 설치 샘플 준비
      """
      시험용 HPE990 Emulator 실행 후 Continue 클릭
      작업을 불러오지 않은 Edger 화면 준비
      관찰 기준: HPE990 GUI 1.22.0, Language English
      Job Manager에 CIRCLE 설치 샘플이 포함된 시험 환경 준비
      """
    And 시험값 유지 및 기록 준비
      """
      기존 사용자 작업 대신 설치 샘플 CIRCLE로 시험
      Job Editor에서 값을 변경하지 않고 Cancel로 복귀
      Digital Pattern에서 도형 변경 조작 없이 Hole Editor로 전환 후 나가기 버튼으로 복귀
      시험 중 화면 변화와 수행 시각 기록
      """
    # Step 1
    When Edger의 폴더 버튼 클릭
    And Job Manager의 설치 샘플 탭 선택
    And CIRCLE 항목 선택
    And Job Manager 하단의 불러오기 버튼 클릭
    Then Edger 화면에 작업 번호와 원형 도형이 보여야 합니다.
    And 하단 Job Editor 아이콘과 작업 옵션 아이콘이 작업 미선택 상태의 회색 표시에서 활성 상태의 표시로 보여야 합니다.
    # Step 2
    When Edger 좌측 하단의 Job Editor 아이콘 클릭
    Then Job Editor 화면이 보여야 합니다.
    # Step 3
    When Job Editor의 Cancel 클릭
    And Edger 우측 하단 패널 상단의 Digital Pattern 아이콘 클릭
    Then Digital Pattern 화면이 보여야 합니다.
    # Step 4
    When Digital Pattern 상단의 Hole Editor 선택
    Then HoleEditor 화면이 보여야 합니다.
    # Step 5
    When HoleEditor의 우측 상단 나가기 버튼 클릭
    Then Edger 화면에 기존 작업 번호와 원형 도형이 유지되어 보여야 합니다.

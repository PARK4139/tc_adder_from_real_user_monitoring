@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/작업%20불러오기/Job%20Manager
Feature: Job Manager 작업 불러오기 검수 TC

  # MCP/RAM 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-270 @observed-behavior @type-navigation
  Scenario: TC-270 CIRCLE 샘플 선택 및 작업 불러오기
    Given Emulator 및 설치 샘플 준비
      """
      시험용 HPE990 Emulator 실행 후 Continue 클릭
      작업을 불러오지 않은 Edger 화면 준비
      관찰 기준: HPE990 GUI 1.22.0, Language English
      Job Manager에 CIRCLE 설치 샘플이 포함된 시험 환경 준비
      """
    And 시험 작업 및 기록 준비
      """
      기존 사용자 작업 대신 설치 샘플 CIRCLE로 시험
      시험 중 화면 변화와 수행 시각 기록
      시험 후 작업 로드 상태 기록
      """
    # Step 1
    When Edger의 폴더 버튼 클릭
    And Job Manager의 설치 샘플 탭 선택
    Then 설치 샘플 목록에 CIRCLE 항목이 보여야 합니다.
    # Step 2
    When CIRCLE 항목 선택
    Then CIRCLE 행이 선택된 상태로 보여야 합니다.
    And 하단 미리보기에 원형 도형이 보여야 합니다.
    And 선택한 샘플의 FPD 67.0, DBL 17.0, Frame Type Pattern 정보가 보여야 합니다.
    # Step 3
    When Job Manager 하단의 폴더·아래 화살표 모양 불러오기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.
    And 작업 번호 영역에 비어 있지 않은 작업 번호가 보여야 합니다.
    And Edger 도형 영역에 불러온 원형 도형이 보여야 합니다.


@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/작업%20불러오기/Job%20Manager
Feature: Job Manager 작업 불러오기 검수 TC

  # MCP/RAM 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-260 @observed-behavior @type-navigation
  Scenario: TC-260 Job Manager 진입 및 설치 샘플 목록 확인
    Given Emulator 초기 화면 준비
      """
      시험용 HPE990 Emulator 실행 후 Continue 클릭
      작업을 불러오지 않은 Edger 화면 준비
      관찰 기준: HPE990 GUI 1.22.0, Language English
      """
    And 설치 샘플 및 기록 준비
      """
      Job Manager에 CIRCLE 설치 샘플이 포함된 시험 환경 준비
      설치 샘플 탭 위치: 상단 탭 영역의 오른쪽 끝 도형 아이콘
      시험 중 화면 변화와 수행 시각 기록
      """
    # Step 1
    When Edger의 폴더 버튼 클릭
    Then Job Manager 화면이 보여야 합니다.
    # Step 2
    When Job Manager의 설치 샘플 탭 선택
    Then 설치 샘플 목록에 CIRCLE 항목이 보여야 합니다.
    And 목록에 Job Number, Type, Frame Type, FPD, DBL 컬럼이 보여야 합니다.
    # Step 3
    When Job Manager의 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.


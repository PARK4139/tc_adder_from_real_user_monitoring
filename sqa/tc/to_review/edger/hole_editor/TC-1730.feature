@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Hole%20Editor
Feature: Edger > Hole Editor 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1730 @type-navigation
  Scenario: TC-1730 화면 진입 및 나가기 확인
    Given 시험 작업의 Digital Pattern 화면
      """
      지정한 시험 작업을 불러온 Edger에서 Digital Pattern 아이콘으로 진입한 상태
      이전 TC의 실행 결과에 의존하지 않고 이 TC의 준비 과정에서 상태 구성
      시험 시작 시 작업 번호와 기대 도형을 비교 기준으로 기록
      예시: 설치 샘플 CIRCLE과 원형 도형
      """
    And 작업값 유지 조건
      """
      Job Editor에서는 값을 변경하지 않고 Cancel로 복귀
      Digital Pattern과 HoleEditor에서는 도형·설정 변경 없이 화면 이동
      """

    # Step 1
    When Digital Pattern 상단의 Hole Editor 선택
    Then HoleEditor 화면이 보여야 합니다.
    # Step 2
    When 우측 상단 나가기 버튼 클릭
    Then HoleEditor 화면이 닫히고 Edger 화면이 보여야 합니다.
    And 작업 번호와 도형이 시험 시작 시 기록한 상태와 일치해야 합니다.

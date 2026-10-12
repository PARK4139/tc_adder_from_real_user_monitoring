@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger
Feature: Edger 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1740 @type-navigation
  Scenario: TC-1740 편집 화면 순회 후 작업 유지 확인
    Given 시험 작업이 불러와진 Edger 화면
      """
      Job Manager에서 지정한 시험 작업을 불러온 상태
      작업 번호와 기대 도형, 편집 화면 진입을 지원하는 작업 조건 확인
      시험 시작 시 작업 번호·도형·속성을 비교 기준으로 기록
      예시: 설치 샘플 CIRCLE과 원형 도형
      """
    And 작업값 유지 조건
      """
      Job Editor에서는 값을 변경하지 않고 Cancel로 복귀
      Digital Pattern과 HoleEditor에서는 도형·설정 변경 없이 화면 이동
      """

    # Step 1
    When 좌측 하단의 Job Editor 아이콘 클릭
    And Job Editor의 Cancel 클릭
    Then Edger 화면이 보여야 합니다.
    # Step 2
    When 우측 하단 패널 상단의 Digital Pattern 아이콘 클릭
    And Digital Pattern 상단의 Hole Editor 선택
    And HoleEditor의 우측 상단 나가기 버튼 클릭
    Then Edger 화면이 보여야 합니다.
    # Step 3
    When 작업 번호 및 도형 확인
    Then 작업 번호와 도형이 시험 시작 시 기록한 상태와 일치해야 합니다.

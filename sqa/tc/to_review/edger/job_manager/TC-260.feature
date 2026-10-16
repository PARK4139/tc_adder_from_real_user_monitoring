@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-260 @type-navigation
  Scenario: TC-260 화면 진입 및 시험 작업 목록 표시 확인
    Given Edger 화면에서 작업 번호와 도형이 비어 있는 상태 확인
    And 불러올 시험 작업의 목록 탭·식별값·기대 도형과 속성값 확인
      """
      Job Manager에서 불러올 수 있는 시험 작업의 식별값과 목록 탭
      시험 작업의 기대 도형, FPD, DBL, Frame Type 값
      기존 사용자 작업을 변경하지 않는 시험 데이터 사용
      예시: 설치 샘플 탭의 CIRCLE, 원형 도형, FPD 67.0, DBL 17.0, Frame Type Pattern
      """

    # Step 1
    When Edger의 폴더 버튼 클릭
    Then Job Manager 화면이 보여야 합니다.
    # Step 2
    When 지정한 시험 작업이 있는 목록 탭 선택
    Then 목록에 지정한 시험 작업 항목이 보여야 합니다.
    And 목록에 Job Number, Type, Frame Type, FPD, DBL 컬럼이 보여야 합니다.
    # Step 3
    When 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.

@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-270 @type-navigation
  Scenario: TC-270 선택한 시험 작업 불러오기
    Given Edger 화면에서 작업 번호와 도형이 비어 있는 상태 확인
    And 불러올 시험 작업의 목록 탭·식별값·기대 도형과 속성값 확인
      """
      Job Manager에서 불러올 수 있는 시험 작업의 식별값과 목록 탭
      시험 작업의 기대 도형, FPD, DBL, Frame Type 값
      기존 사용자 작업을 변경하지 않는 시험 데이터 사용
      예시: 설치 샘플 탭의 CIRCLE, 원형 도형, FPD 67.0, DBL 17.0, Frame Type Pattern
      """
    And Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 지정한 시험 작업이 있는 목록 탭 선택
    And 지정한 시험 작업 항목 선택
    And 시험 작업 항목의 선택 상태 확인

    # Step 1
    When 하단의 폴더·아래 화살표 모양 불러오기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.
    # Step 2
    When Edger의 작업 번호 및 도형 영역 확인
    Then 작업 번호 영역에 비어 있지 않은 작업 번호가 보여야 합니다.
    And 도형 영역에 시험 작업의 기대 도형이 보여야 합니다.

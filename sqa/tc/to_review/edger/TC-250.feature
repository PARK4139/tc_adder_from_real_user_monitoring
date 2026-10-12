@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger
Feature: Edger 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-250 @type-navigation
  Scenario: TC-250 작업 미선택 시 작업 번호·도형·편집 UI 상태 확인
    Given 작업 미선택 상태
      """
      작업 번호와 도형이 비어 있는 Edger 화면
      """

    # Step 1
    When 작업 번호 영역 및 도형 영역 확인
    Then 작업 번호 영역에 불러온 작업 번호가 없는 상태로 보여야 합니다.
    And 도형 영역에 작업 도형이 없는 상태로 보여야 합니다.
    # Step 2
    When 하단 Job Editor 아이콘 및 작업 옵션 영역 확인
    Then Job Editor 아이콘과 작업 옵션 영역이 회색 상태로 보여야 합니다.

@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1690 @type-navigation
  Scenario: TC-1690 시험 작업 선택 및 미리보기 확인
    Given Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택

    # Step 1
    When CIRCLE 작업 선택
    Then CIRCLE 작업 행이 선택된 상태로 보여야 합니다.
    # Step 2
    When 하단 미리보기 및 작업 정보 확인
    Then 미리보기에 원형 도형이 보여야 합니다.
    And FPD에 67.0, DBL에 17.0, Frame Type에 Pattern이 보여야 합니다.
    # Step 3
    When 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.

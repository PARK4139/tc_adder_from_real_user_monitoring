@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Editor
Feature: Edger > Job Editor 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1710 @type-navigation
  Scenario: TC-1710 화면 진입 및 Cancel 복귀 확인
    Given Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택
    And CIRCLE 작업 선택
    And 불러오기 버튼 클릭
    And Edger 화면에서 불러온 작업 번호와 원형 도형 확인

    # Step 1
    When Edger 좌측 하단의 Job Editor 아이콘 클릭
    Then Job Editor 화면이 보여야 합니다.
    # Step 2
    When Cancel 클릭
    Then Job Editor 화면이 닫히고 Edger 화면이 보여야 합니다.
    And 작업 번호와 원형 도형이 사전조건에서 확인한 값과 같아야 합니다.

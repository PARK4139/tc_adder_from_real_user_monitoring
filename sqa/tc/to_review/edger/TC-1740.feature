@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger
Feature: Edger 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1740 @type-navigation
  Scenario: TC-1740 편집 화면 순회 후 작업 유지 확인
    Given Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택
    And CIRCLE 작업 선택
    And 불러오기 버튼 클릭
    And Edger 화면에서 불러온 작업 번호와 원형 도형 확인

    # Step 1
    When 좌측 하단의 Job Editor 아이콘 클릭
    And Job Editor의 Cancel 클릭
    Then Edger 화면이 보여야 합니다.
    # Step 2
    When 우측 하단 패널 상단의 Digital Pattern 아이콘 클릭
    And Digital Pattern 상단의 Hole Editor 선택
    And Hole Editor 우측 상단 나가기 버튼 클릭
    Then Edger 화면이 보여야 합니다.
    # Step 3
    When 작업 번호 및 도형 확인
    Then 작업 번호와 원형 도형이 사전조건에서 확인한 값과 같아야 합니다.

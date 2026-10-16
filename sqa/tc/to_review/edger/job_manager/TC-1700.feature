@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1700 @type-navigation
  Scenario: TC-1700 불러오기 없이 나가기 및 작업 미선택 상태 유지 확인
    Given Job을 불러오지 않은 Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택

    # Step 1
    When CIRCLE 작업 선택
    And 불러오기 버튼을 선택하지 않고 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.
    # Step 2
    When Edger의 작업 번호·도형·편집 UI 상태 확인
    Then 작업 번호 영역과 도형 영역은 작업 미선택 상태로 보여야 합니다.
    And Job Editor 아이콘과 작업 옵션 영역이 회색 상태로 보여야 합니다.

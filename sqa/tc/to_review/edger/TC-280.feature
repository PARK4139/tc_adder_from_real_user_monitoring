@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger
Feature: Edger 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-280 @type-navigation
  Scenario: TC-280 작업 불러오기 후 편집 UI 활성화 확인
    Given Edger 화면에서 작업 번호와 도형이 비어 있는 상태 확인
    And Job Editor 아이콘과 작업 옵션 영역의 회색 표시 확인
    And 불러올 시험 작업의 목록 탭·식별값·기대 도형과 속성값 확인
      """
      Job Manager에서 불러올 수 있는 시험 작업의 식별값과 목록 탭
      시험 작업의 기대 도형, FPD, DBL, Frame Type 값
      기존 사용자 작업을 변경하지 않는 시험 데이터 사용
      예시: 설치 샘플 탭의 CIRCLE, 원형 도형, FPD 67.0, DBL 17.0, Frame Type Pattern
      """

    # Step 1
    When Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 지정한 시험 작업이 있는 목록 탭 선택
    And 지정한 시험 작업 항목 선택
    And Job Manager 하단의 불러오기 버튼 클릭
    Then Edger 화면에 비어 있지 않은 작업 번호와 시험 작업의 기대 도형이 보여야 합니다.
    # Step 2
    When Edger 우측 하단 패널의 Job Editor 아이콘과 작업 옵션 영역 확인
    Then Job Editor 아이콘과 작업 옵션 영역이 사전조건에서 확인한 회색 표시에서 활성 상태의 표시로 보여야 합니다.

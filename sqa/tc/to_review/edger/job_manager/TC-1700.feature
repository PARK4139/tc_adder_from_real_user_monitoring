@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1700 @type-navigation
  Scenario: TC-1700 불러오기 없이 나가기 및 작업 미선택 상태 유지 확인
    Given 작업 미선택 상태에서 진입한 Job Manager 화면
      """
      Edger의 폴더 버튼으로 Job Manager에 진입하고 지정한 시험 작업의 목록 탭을 연 상태
      이전 TC의 실행 결과에 의존하지 않고 이 TC의 준비 과정에서 상태 구성
      """
    And 시험 작업 지정
      """
      Job Manager에서 불러올 수 있는 시험 작업의 식별값과 목록 탭 지정
      기대 도형, FPD, DBL, Frame Type 값 지정
      기존 사용자 작업을 변경하지 않는 시험 데이터 사용
      예시: 설치 샘플 탭의 CIRCLE, 원형 도형, FPD 67.0, DBL 17.0, Frame Type Pattern
      """

    # Step 1
    When 지정한 시험 작업 항목 선택
    And 불러오기 버튼을 클릭하지 않고 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.
    # Step 2
    When Edger의 작업 번호·도형·편집 UI 상태 확인
    Then 작업 번호 영역과 도형 영역은 작업 미선택 상태로 보여야 합니다.
    And Job Editor 아이콘과 작업 옵션 영역이 회색 상태로 보여야 합니다.

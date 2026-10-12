@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger > Job Manager 검수 TC

  # TC-250~TC-280의 관찰 흐름에서 검증 목적별로 분리한 초안. 분리 후 TC는 미실행.
  # 기존 MCP 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/interactive-audit/
  @TC-1690 @type-navigation
  Scenario: TC-1690 시험 작업 선택 및 미리보기 확인
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
    Then 지정한 시험 작업 행이 선택된 상태로 보여야 합니다.
    # Step 2
    When 하단 미리보기 및 작업 정보 확인
    Then 미리보기에 시험 작업의 기대 도형이 보여야 합니다.
    And FPD, DBL, Frame Type이 지정한 시험 작업의 값과 일치해야 합니다.
    # Step 3
    When 우측 상단 나가기 버튼 클릭
    Then Job Manager 화면이 닫히고 Edger 화면이 보여야 합니다.

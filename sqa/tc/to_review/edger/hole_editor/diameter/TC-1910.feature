@draft @ISSUE-50c688e3 @AC-route-ui-validation @path-Edger/HoleEditor/DIAMETER
Feature: DIAMETER 입력 모달 진입 및 기존 값 확정 (숫자 입력)

# collection-route: HoleEditor/DIAMETER
# MCP 진입·복귀 수집 증거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\50c688e3\collection-1791768102158616900\hole-inputs\routes.json
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1910 @type-number
  Scenario: TC-1910 DIAMETER 입력 모달 진입 및 기존 값 확정 (숫자 입력)
    Given Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택
    And NEW_DRILL_STD_PATTERN 작업 선택
    And 불러오기 버튼 클릭
    And Edger 우측 하단 패널 상단의 Digital Pattern 아이콘 클릭
    And Digital Pattern 상단의 Hole Editor 선택
    And Job ID 001 홀 선택 및 DIAMETER 기존 값 1.00 확인

    # Step 1
    When Hole Editor의 DIAMETER 항목 클릭
    Then DIAMETER 숫자 입력 키패드 모달이 보여야 합니다.
    And 입력란에 선택한 홀의 기존 DIAMETER 값이 보여야 합니다.
    And 유효범위 0.80~5.00과 현재 값 1.00이 보여야 합니다.

    # Step 2
    When 입력값을 변경하지 않고 키패드의 ↵ 버튼 클릭
    Then DIAMETER 모달이 닫히고 Hole Editor 화면이 보여야 합니다.

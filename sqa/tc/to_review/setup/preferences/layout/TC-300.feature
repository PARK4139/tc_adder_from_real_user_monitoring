@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Layout
Feature: Edger > Setup > Preferences > Layout 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-300 @type-scroll
  Scenario: TC-300 Layout 스크롤 및 설정값 유지
    # Step 1
    When Setup > Preferences > Layout 탭 선택
    And Layout 설정 영역 최상단 스크롤
    Then Default Side 항목이 보여야 합니다.
    # Step 2
    When Layout 설정 영역 최하단 스크롤
    Then Mandatory Field Warning > Bridge Size 항목과 Save, Cancel 버튼이 보여야 합니다.
    # Step 3
    When Layout 설정 영역 최상단 스크롤
    Then Default Side 항목과 시험 전 값이 유지되어 보여야 합니다.

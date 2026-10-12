@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Digital%20Pattern
Feature: Edger > Setup > Preferences > Digital Pattern 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-1130 @type-navigation
  Scenario: TC-1130 Digital Pattern 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Digital Pattern 탭 선택
    Then Preferences 창의 Digital Pattern 탭이 선택 상태로 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And Digital Pattern Apply Method
    And Zoom Ratio
    And Save
    And Cancel

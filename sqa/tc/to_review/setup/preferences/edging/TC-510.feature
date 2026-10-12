@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Edging
Feature: Edger > Setup > Preferences > Edging 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-510 @type-scroll
  Scenario: TC-510 Edging 스크롤 및 설정값 유지
    # Step 1
    When Setup > Preferences > Edging 탭 선택
    And Edging 설정 영역 최상단 스크롤
    Then Edging Start Side 항목이 보여야 합니다.
    # Step 2
    When Edging 설정 영역 최하단 스크롤
    Then Hydrophobic Mode > Default Value > Box Center Clamp Pressure 항목과 Save, Cancel 버튼이 보여야 합니다.
    # Step 3
    When Edging 설정 영역 최상단 스크롤
    Then Edging Start Side 항목과 시험 전 값이 유지되어 보여야 합니다.

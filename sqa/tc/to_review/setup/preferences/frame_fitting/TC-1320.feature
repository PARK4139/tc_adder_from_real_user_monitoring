@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Frame%20Fitting
Feature: Edger > Setup > Preferences > Frame Fitting 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-1320 @type-navigation
  Scenario: TC-1320 Frame Fitting 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Frame Fitting 탭 선택
    And Frame Fitting 설정 영역 상단부터 하단까지 스크롤
    Then Preferences 창의 Frame Fitting 탭이 선택 상태로 보여야 합니다.
    And 스크롤 영역은 각 요소 위치에 도달했을 때 해당 요소가 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And Master Size
    And Metal > Horizontal
    And Metal > Vertical
    And Hard Plastic > Horizontal
    And Hard Plastic > Vertical
    And Soft Plastic > Horizontal
    And Soft Plastic > Vertical
    And Ultem > Horizontal
    And Ultem > Vertical
    And Pattern > Horizontal
    And Pattern > Vertical
    And Step Bevel > Horizontal
    And Step Bevel > Vertical
    And Save
    And Cancel

@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Hole%20Editor
Feature: Edger > Setup > Preferences > Hole Editor 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-1180 @type-navigation
  Scenario: TC-1180 Hole Editor 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Hole Editor 탭 선택
    Then Preferences 창의 Hole Editor 탭이 선택 상태로 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And 상단 무라벨 필드
    And Hole Diameter
    And Angle Default Options > Tilting Mode
    And Angle Default Options > Auto Tilting Reference Surface
    And Angle Default Options > User Defined Tilting Angle
    And Position Display > X Pos Reference
    And Position Display > Y Pos Reference
    And Position Display > Slot End Pos Display
    And Preset Hole Data Load
    And Rect Slot
    And Notch Length Optimizer
    And Save
    And Cancel

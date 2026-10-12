@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Layout
Feature: Edger > Setup > Preferences > Layout 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-290 @type-navigation
  Scenario: TC-290 Layout 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Layout 탭 선택
    And Layout 설정 영역 상단부터 하단까지 스크롤
    Then Preferences 창의 Layout 탭이 선택 상태로 보여야 합니다.
    And 스크롤 영역은 각 요소 위치에 도달했을 때 해당 요소가 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And Default Side
    And Lens Type
    And Blocking Mode
    And OH Sync
    And OH Type
    And Default Value > PD
    And Default Value > Bridge Size
    And Default Value > Delta Y
    And Default Value > Boxed Height
    And Default Value > Mixed Height
    And Default Value > Bifocal Offset (Horizontal)
    And Default Value > Bifocal Offset (Vertical)
    And Default Value > Near Segment Diameter
    And Mandatory Field Warning
    And Mandatory Field Warning > PD
    And Mandatory Field Warning > OH
    And Mandatory Field Warning > Bridge Size
    And Save
    And Cancel

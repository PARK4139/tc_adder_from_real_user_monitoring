@draft @ISSUE-50c688e3 @AC-route-ui-validation @path-Edger/Setup/Touchscreen%20Check
Feature: 화면 진입 및 표시 확인

# collection-route: Touchscreen Check
# MCP 진입·복귀 수집 증거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\50c688e3\collection-1791768102158616900\setup-routes-4\routes.json
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1790 @type-navigation
  Scenario: TC-1790 화면 진입 및 표시 확인
    Given Edger 화면에서 Setup 버튼 클릭

    # Step 1
    When Setup > Touchscreen Check 버튼 클릭
    Then Touchscreen Check 화면이 보여야 합니다.
    When Touchscreen Check 화면의 Close 버튼 클릭
    Then Setup 화면이 보여야 합니다.

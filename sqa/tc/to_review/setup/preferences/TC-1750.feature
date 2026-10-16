@draft @ISSUE-50c688e3 @AC-route-ui-validation @path-Edger/Setup/Preferences
Feature: 화면 진입 및 Setup 복귀 확인

# collection-route: Preferences
# MCP 진입·복귀 수집 증거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\50c688e3\collection-1791768102158616900\setup-routes-4\routes.json
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1750 @type-navigation
  Scenario: TC-1750 화면 진입 및 Setup 복귀 확인
    Given Edger 화면에서 Setup 버튼 클릭

    # Step 1
    When Setup > Preferences 버튼 클릭
    Then Preferences 화면의 설정 영역과 Save·Cancel 버튼이 보여야 합니다.

    # Step 2
    When Preferences 화면의 Cancel 버튼 클릭
    Then Setup 화면이 보여야 합니다.

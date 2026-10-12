@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Comm.%20Port
Feature: Edger > Setup > Preferences > Comm. Port 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
# 수집 요소 참조: UI-026496 (라벨 또는 값 관측 ID; 편집 컨트롤 매핑 확정 아님)
  @TC-1670 @type-button @requires-specification @spec-test-value @spec-save-display
  Scenario: TC-1670 Comm. Port Save 버튼의 설정 저장 (버튼)
    And 설정값 복구 준비
      """
      시험 전 해당 항목과 연관된 설정의 원래 값 기록
      시험 후 원래 값 저장 및 재진입 확인 방법 기록
      실장비 가공·통신 실행 없이 시험용 Emulator에서 설정 확인
      """
    # Step 1
    When Setup > Preferences > Comm. Port 탭 선택
    Then Preferences 창의 Comm. Port 탭과 Save 버튼이 보여야 합니다.
    # Step 2
    When BARCODE의 승인된 시험값 체크 상태 변경
    Then BARCODE에 승인된 시험값이 보여야 합니다.
    # Step 3
    When Save 클릭
    Then Preferences 창이 닫히고 Setup 화면이 보여야 합니다.
    # Step 4
    When Setup > Preferences > Comm. Port 탭 선택
    And BARCODE 항목 확인
    Then BARCODE에 저장한 시험값이 보여야 합니다.
    # Step 5
    When BARCODE 항목과 연관 설정의 원래 값 복원
    And Save 클릭
    And Setup > Preferences > Comm. Port 탭 선택
    And BARCODE 항목 확인
    Then 시험 전 설정 상태가 유지되어 보여야 합니다.

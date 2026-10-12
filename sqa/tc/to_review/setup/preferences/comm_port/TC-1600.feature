@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Comm.%20Port
Feature: Edger > Setup > Preferences > Comm. Port 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
# 수집 요소 참조: UI-026651 (라벨 또는 값 관측 ID; 편집 컨트롤 매핑 확정 아님)
# 추가 MCP 선택 목록 근거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\ui\5a6c0a26ee604ff58eb87bc12bbfcba7\fa8176142e744a5b88a1584d5df85af7\inventory.json
# 목록 문구는 원본 PNG 확인; 선택값 변경·Save·재진입 시험 미실행.
  @TC-1600 @type-option-selector @requires-specification @spec-save-display @spec-test-value
  Scenario: TC-1600 Job Request > Delete Existing Job Before Requesting 선택 및 저장값 확인 (선택기)
    And 설정값 복구 준비
      """
      시험 전 해당 항목과 연관된 설정의 원래 값 기록
      시험 후 원래 값 저장 및 재진입 확인 방법 기록
      실장비 가공·통신 실행 없이 시험용 Emulator에서 설정 확인
      """
    # Step 1
    When Setup > Preferences > Comm. Port 탭 선택
    And Job Request > Delete Existing Job Before Requesting 위치로 스크롤
    Then Job Request > Delete Existing Job Before Requesting 항목과 현재 설정 상태가 보여야 합니다.
    # Step 2
    When Job Request > Delete Existing Job Before Requesting 클릭
    Then 선택 목록에 OFF, ON 항목이 보여야 합니다.
    # Step 3
    When Job Request > Delete Existing Job Before Requesting의 승인된 시험값 선택
    Then Job Request > Delete Existing Job Before Requesting에 선택한 시험값이 보여야 합니다.
    # Step 4
    When Save 클릭
    And Setup > Preferences > Comm. Port 탭 선택
    And Job Request > Delete Existing Job Before Requesting 항목 확인
    Then Job Request > Delete Existing Job Before Requesting에 마지막으로 확정한 설정값이 유지되어 보여야 합니다.
    # Step 5
    When Job Request > Delete Existing Job Before Requesting 항목과 연관 설정의 원래 값 복원
    And Save 클릭
    And Setup > Preferences > Comm. Port 탭 선택
    And Job Request > Delete Existing Job Before Requesting 항목 확인
    Then Job Request > Delete Existing Job Before Requesting 항목과 연관 설정이 시험 전 상태와 일치해야 합니다.

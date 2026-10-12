@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Frame%20Fitting
Feature: Edger > Setup > Preferences > Frame Fitting 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
# 수집 요소 참조: UI-026612 (라벨 또는 값 관측 ID; 편집 컨트롤 매핑 확정 아님)
# ↵ 버튼 클릭 수집 검증: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\ui\5a6c0a26ee604ff58eb87bc12bbfcba7\aa114d3e4d9b412aa3435978c3242189\inventory.json
# 추가 MCP 팝업 근거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\ui\5a6c0a26ee604ff58eb87bc12bbfcba7\445ad7533a9d48f99ef606cdb5f54cac\inventory.json
# 입력 컨트롤: UI-025704; 팝업: UI-029620
# 터치스크린 기준: ESC·Enter 키를 사용자 조작 절차로 사용하지 않음. 숫자 모달은 ↵ 버튼 클릭.
# 팝업 관찰만 완료; 시험값 입력·저장·재진입 및 BDD 실행은 미검증.
  @TC-1350 @type-number @requires-specification @spec-save-display @spec-input-format @spec-test-value
  Scenario: TC-1350 Metal > Horizontal 입력 및 저장값 확인 (숫자 입력란)
    And 설정값 복구 준비
      """
      시험 전 해당 항목과 연관된 설정의 원래 값 기록
      시험 후 원래 값 저장 및 재진입 확인 방법 기록
      실장비 가공·통신 실행 없이 시험용 Emulator에서 설정 확인
      """
    # Step 1
    When Setup > Preferences > Frame Fitting 탭 선택
    And Metal > Horizontal 위치로 스크롤
    Then Metal > Horizontal 항목과 현재 설정 상태가 보여야 합니다.
    # Step 2
    When Metal > Horizontal 선택
    Then 숫자 입력 모달과 현재 값, 숫자 버튼, ↵ 버튼이 보여야 합니다.
    # Step 3
    When 숫자 입력 모달의 기존 값 삭제
    And 승인된 시험값에 해당하는 화면 숫자·소수점 버튼 클릭
    And ↵ 버튼 클릭
    Then Metal > Horizontal에 입력한 시험값이 보여야 합니다.
    # Step 4
    When Save 클릭
    And Setup > Preferences > Frame Fitting 탭 선택
    And Metal > Horizontal 항목 확인
    Then Metal > Horizontal에 마지막으로 확정한 설정값이 유지되어 보여야 합니다.
    # Step 5
    When Metal > Horizontal 선택
    And 화면 키패드로 원래 값 입력
    And ↵ 버튼 클릭
    And 연관 설정의 원래 값 복원
    And Save 클릭
    And Setup > Preferences > Frame Fitting 탭 선택
    And Metal > Horizontal 항목 확인
    Then Metal > Horizontal 항목과 연관 설정이 시험 전 상태와 일치해야 합니다.

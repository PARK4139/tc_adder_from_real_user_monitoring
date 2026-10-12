@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Edging
Feature: Edger > Setup > Preferences > Edging 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
# 수집 요소 참조: UI-026545 (라벨 또는 값 관측 ID; 편집 컨트롤 매핑 확정 아님)
  @TC-560 @type-radio @requires-specification @spec-save-display
  Scenario: TC-560 Edging Type > Frame (Metal) 선택 및 저장값 확인 (라디오 버튼)
    And 설정값 복구 준비
      """
      시험 전 해당 항목과 연관된 설정의 원래 값 기록
      시험 후 원래 값 저장 및 재진입 확인 방법 기록
      실장비 가공·통신 실행 없이 시험용 Emulator에서 설정 확인
      """
    # Step 1
    When Setup > Preferences > Edging 탭 선택
    And Edging Type > Frame (Metal) 위치로 스크롤
    Then Edging Type > Frame (Metal) 항목과 현재 설정 상태가 보여야 합니다.
    # Step 2
    When Edging Type > Frame (Metal) 선택 항목 확인
    Then Edging Type > Frame (Metal)에 Bevel, Flat, Groove 항목이 보여야 합니다.
    # Step 3
    When Edging Type > Frame (Metal)의 Bevel 선택
    Then Edging Type > Frame (Metal)의 Bevel만 선택 상태로 보여야 합니다.
    # Step 4
    When Edging Type > Frame (Metal)의 Flat 선택
    Then Edging Type > Frame (Metal)의 Flat만 선택 상태로 보여야 합니다.
    # Step 5
    When Edging Type > Frame (Metal)의 Groove 선택
    Then Edging Type > Frame (Metal)의 Groove만 선택 상태로 보여야 합니다.
    # Step 6
    When Save 클릭
    And Setup > Preferences > Edging 탭 선택
    And Edging Type > Frame (Metal) 항목 확인
    Then Edging Type > Frame (Metal)에 마지막으로 확정한 설정값이 유지되어 보여야 합니다.
    # Step 7
    When Edging Type > Frame (Metal) 항목과 연관 설정의 원래 값 복원
    And Save 클릭
    And Setup > Preferences > Edging 탭 선택
    And Edging Type > Frame (Metal) 항목 확인
    Then Edging Type > Frame (Metal) 항목과 연관 설정이 시험 전 상태와 일치해야 합니다.

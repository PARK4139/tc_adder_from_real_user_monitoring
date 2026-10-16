@draft @requires-specification @ISSUE-50c688e3 @AC-depth-prefill-validation @path-Edger/Hole%20Editor/DEPTH
Feature: DEPTH 기존 음수 값과 유효범위 표시 확인 (숫자 입력)

# collection-finding: HoleEditor/DEPTH-original-outside-range
# 관찰 근거: {D_TEMP}/hpe990/evidence/50c688e3/collection-1791768102158616900/hole-inputs/routes.json
# 관찰값: 기존 값 -0.20, 표시 범위 0.00~6.00. 확정 시 모달 유지. 사양 일치 판정 아님.
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1940 @type-number @requires-specification @spec-error-handling @spec-input-format @actual-behavior-check
  Scenario: TC-1940 DEPTH 기존 음수 값과 유효범위 표시 확인 (숫자 입력)
    Given Job ID 001인 NEW_DRILL_STD_PATTERN 작업의 Hole Editor 화면에서 DEPTH 버튼 클릭

    # Step 1
    When Hole Editor의 DEPTH 항목 클릭
    Then DEPTH 숫자 입력 키패드 모달이 보여야 합니다.
    And 입력란에 -0.20과 유효범위 0.00~6.00이 보여야 합니다.

    # Step 2
    When 키보드 Escape 키 입력
    Then DEPTH 입력 모달이 닫히고 Hole Editor 화면이 보여야 합니다.

    # 사양 미확정: -0.20의 확정 허용 여부와 오류 표시 기준을 확인하기 전까지 실행 판정 보류.

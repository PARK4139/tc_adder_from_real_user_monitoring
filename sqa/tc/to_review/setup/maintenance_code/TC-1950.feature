@draft @ISSUE-50c688e3 @AC-maintenance-keypad-input @path-Edger/Setup/Maintenance%20Code
Feature: 유효범위 내 양수·음수·0 입력 확인 (숫자 입력)

# collection-validation: Maintenance-Code/in-range-keypad
# 관찰 증거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\50c688e3\collection-1791768102158616900\maintenance-range
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1950 @type-number
  Scenario: TC-1950 유효범위 내 양수·음수·0 입력 확인 (숫자 입력)
    Given Edger 화면에서 Setup 버튼 클릭

    # Step 1
    When Setup > Maintenance 버튼 클릭
    Then Maintenance Code 키패드 모달이 보여야 합니다.
    And 유효범위 -999999999~999999999가 보여야 합니다.

    # Step 2
    When 키패드의 1 버튼 클릭
    Then 입력란에 1이 보여야 합니다.

    # Step 3
    When 키패드의 +/- 버튼 클릭
    Then 입력란에 -1이 보여야 합니다.

    # Step 4
    When 키패드의 원형 화살표 버튼 클릭
    And 키패드의 0 버튼 클릭
    Then 입력란에 0이 보여야 합니다.

    # Step 5
    When 키패드의 원형 화살표 버튼 클릭
    And Enter를 누르지 않고 Escape로 모달 닫기
    Then Maintenance Code 모달이 닫히고 Setup 화면이 보여야 합니다.

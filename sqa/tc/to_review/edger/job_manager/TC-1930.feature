@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger Job Manager 취소 흐름 검수

  @TC-1930 @type-navigation
  Scenario: TC-1930 선택한 시험 Job을 불러오지 않고 나가기
    Given 작업 미선택 상태
      """
      작업 번호와 도형이 비어 있는 Edger 화면
      """
    And 승인된 시험 Job 지정
      """
      고객 작업을 변경하지 않는 시험 Job과 목록 탭
      Job Number, Type, Frame Type, FPD, DBL의 기대값 기록
      """

    # Step 1
    When 작업 번호·도형·Job Editor 조작 영역 확인
    Then 작업 번호와 도형이 비어 있고 Job Editor 조작 영역이 비활성 상태여야 합니다.
    # Step 2
    When Edger의 폴더 버튼을 눌러 Job Manager를 열고 지정한 목록 탭 선택
    Then 지정한 시험 Job과 Job Number, Type, Frame Type, FPD, DBL 항목이 보여야 합니다.
    # Step 3
    When 지정한 시험 Job 선택
    Then 선택한 Job의 미리보기와 기록한 Job 속성 기대값이 보여야 합니다.
    # Step 4
    When 시험 Job을 불러오지 않고 Job Manager를 나감
    Then Edger 화면으로 복귀하고 작업 미선택 상태와 비활성 편집 영역이 유지되어야 합니다.

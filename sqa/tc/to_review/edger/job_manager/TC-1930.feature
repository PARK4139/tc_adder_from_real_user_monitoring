@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger Job Manager 취소 흐름 검수

  @TC-1930 @type-navigation
  Scenario: TC-1930 선택한 시험 Job을 불러오지 않고 나가기
    Given Job을 불러오지 않은 Edger 화면에서 작업 번호·도형·Job Editor 조작 영역 확인
    And 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택

    # Step 1
    # Step 2
    When CIRCLE 작업 선택
    Then CIRCLE 작업 행이 선택 상태로 보여야 합니다.
    # Step 3
    When 하단 미리보기와 작업 정보 확인
    Then 원형 도형, FPD 67.0, DBL 17.0, Frame Type Pattern이 보여야 합니다.
    # Step 4
    When 불러오기 버튼을 선택하지 않고 우측 상단 나가기 버튼 클릭
    Then Edger 화면으로 복귀해야 합니다.
    And 작업 번호와 도형이 비어 있어야 합니다.
    And Job Editor 아이콘과 작업 옵션 영역이 회색 상태로 보여야 합니다.

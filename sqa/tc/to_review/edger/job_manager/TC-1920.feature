@draft @ISSUE-def19f18 @AC-hybrid-suite-review @path-Edger/Job%20Manager
Feature: Edger Job 불러오기 흐름 검수

  @TC-1920 @type-navigation
  Scenario: TC-1920 시험 Job 불러오기와 편집 가능 상태 확인
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
    When 불러오기 버튼 클릭
    Then 작업 번호와 원형 도형이 Edger에 보여야 합니다.
    And Job Editor 아이콘과 작업 옵션 영역이 활성화되어 보여야 합니다.
    # Step 5
    When Job Editor 아이콘 클릭
    And Cancel 클릭
    And 우측 하단 패널 상단의 Digital Pattern 아이콘 클릭
    And Digital Pattern 상단의 Hole Editor 선택
    And Hole Editor 우측 상단 나가기 버튼 클릭
    Then Edger 화면에 작업 번호와 원형 도형이 계속 보여야 합니다.
    And Job Editor 아이콘과 작업 옵션 영역이 활성화 상태를 유지해야 합니다.

@draft @ISSUE-50c688e3 @AC-route-ui-validation @path-Edger/Job%20Editor/PD
Feature: PD 입력 모달 진입 및 기존 값 확정 (숫자 입력)

# collection-route: Job Editor/PD
# MCP 진입·복귀 수집 증거: C:\Users\Huvitz\Desktop\Temp\hpe990\evidence\50c688e3\collection-1791768102158616900\job-editor-inputs\routes.json
# 기존 관찰 근거를 유지한 문구 수정이며 자동화 BDD 실행 결과가 아닙니다.
  @TC-1900 @type-number
  Scenario: TC-1900 PD 입력 모달 진입 및 기존 값 확정 (숫자 입력)
    Given Edger 화면에서 폴더 버튼 클릭
    And Job Manager에서 설치 샘플 탭 선택
    And CIRCLE 작업 선택
    And 불러오기 버튼 클릭
    And Edger 화면에서 작업 번호와 도형 확인
    And Edger 우측 하단 패널의 Job Editor 아이콘 클릭
    And PD 항목의 시험 전 값 확인

    # Step 1
    When Job Editor의 PD 항목 클릭
    Then PD 숫자 입력 키패드 모달이 보여야 합니다.
    And 입력란에 사전조건에서 확인한 기존 값이 보여야 합니다.

    # Step 2
    When 입력값을 변경하지 않고 키패드의 ↵ 버튼 클릭
    Then 숫자 입력 모달이 닫히고 Job Editor 화면이 보여야 합니다.

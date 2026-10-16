# 입력유형별 TC Step 템플릿

현재 TC에서 추출한 작성 초안. 실제 실행 결과 없음.

## option-selector

근거: TC-030

{name} 설정 및 적용 확인 (선택기)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>시험 전 {name}가 {first_value}인 상태 준비<br>원래 선택값와 시험 후 {first_value} 복원 방법 기록 |
| 2 | {name} 실동작 관찰 준비<br>HPE990 GUI 1.22.0 관찰 기반으로 {first_value}/{second_value} 전환 범위 확인<br>native RAM과 화면·문구 Real Activity Monitoring 활성 상태 확인<br>언어 목록·선택값·메뉴·환경 설정의 전후 이미지 및 시각 기록<br>다른 설정 항목은 변경하지 않은 상태 준비 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name} 클릭 | 언어 목록 팝업이 펼쳐져 보여야 합니다.<br>{first_value}, {second_value}, Russian, French, German, Japanese, Chinese, Polish, Spanish, Italian, Bulgarian, Portuguese 항목이 보여야 합니다. |
| 3 | {second_value} 선택 | {name}에 {second_value}이 보여야 합니다.<br>언어 목록 팝업이 닫혀야 합니다. |
| 4 | {save_action} | Preferences 창이 닫혀야 합니다.<br>Setup 화면 제목에 메뉴가 보여야 합니다.<br>메뉴 화면에 환경 설정, 시간 설정, 터치스크린 검사 항목이 보여야 합니다. |
| 5 | 메뉴 &gt; 환경 설정 &gt; 일반 탭 선택 | 언어 항목에 한국어가 유지되어 보여야 합니다.<br>환경 설정 화면에 일반, 언어, 저장, 취소 문구가 보여야 합니다. |
| 6 | 언어 클릭 후 영어 선택<br>저장 클릭 | 환경 설정 창이 닫혀야 합니다.<br>메뉴 화면 제목에 Setup이 보여야 합니다.<br>Preferences, Date &amp; Time, Touch Test 항목이 보여야 합니다. |
| 7 | {path} | {name}에 시험 전 값인 {first_value}가 유지되어 보여야 합니다.<br>Preferences 화면에 General, {name}, Save, Cancel 문구가 보여야 합니다. |

TC-030 Language의 English/Korean 관찰 기반. 언어별 메뉴 문구와 적용 흐름은 다른 선택기의 요구사항이 아니며 재사용 전 대상별 기대 결과를 검토해야 함.

## input-field

근거: TC-210

{name} 입력 및 저장값 확인 (입력란)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>{name}의 원래 값 기록<br>시험 후 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {scroll_to_element} | {name} 항목과 입력란이 보여야 합니다. |
| 3 | {name} 입력란 선택 | {name} 값을 편집할 수 있는 입력 상태가 보여야 합니다. |
| 4 | {name}에 {value} 입력<br>입력 확정 | {name} 입력란에 입력한 시험값이 보여야 합니다. |
| 5 | {save_action}<br>{reopen_action}<br>{tab_select_action}<br>{scroll_to_element} | {name} 입력란에 저장한 시험값이 보여야 합니다. |
| 6 | {name} 입력값을 기록한 원래 값으로 복원<br>{save_action}<br>{reopen_action}<br>{tab_select_action}<br>{scroll_to_element} | {name} 값이 시험 전 값과 일치한다 |

TC-030의 편집 가능 가정은 미검증. STATIC_DATA에는 적용하지 않고 표시 템플릿 사용.

## number

근거: TC-070

{name} 숫자 입력 및 저장값 확인 (숫자 입력란)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name} 입력요소 선택 | {name}의 값을 편집할 수 있는 입력 상태가 보여야 합니다. |
| 3 | {name}에 {value} 입력<br>입력 확정 | {name}에 입력한 시험값이 보여야 합니다. |
| 4 | {save_action}<br>{reopen_action}<br>{tab_select_action} | {name}에 저장한 시험값이 보여야 합니다. |
| 5 | {name}의 입력값을 기록한 원래 값으로 복원<br>{save_action}<br>{reopen_action}<br>{tab_select_action} | {name}의 값이 시험 전 값과 일치한다 |

## checkbox

근거: TC-060

{name} 체크 상태 변경 및 저장값 확인 (체크박스)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name}의 체크 해제 | {name}가 체크 해제 상태로 보여야 합니다. |
| 3 | {name} 체크 | {name}가 체크 상태로 보여야 합니다. |
| 4 | {save_action}<br>{reopen_action}<br>{tab_select_action} | {name}가 체크 상태로 보여야 합니다. |
| 5 | {name}를 기록한 원래 체크 상태로 복원<br>{save_action}<br>{reopen_action}<br>{tab_select_action} | {name}의 체크 상태가 시험 전 값과 일치한다 |

## radio

근거: TC-040

{name} 선택 및 저장값 확인 (라디오 버튼)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name}에서 {first_value} 항목 선택 | {name}의 {first_value} 항목이 선택되어 보여야 합니다.<br>{second_value} 항목은 선택 해제되어 보여야 합니다. |
| 3 | {name}에서 {second_value} 항목 선택 | {name}의 {second_value} 항목이 선택되어 보여야 합니다.<br>{first_value} 항목은 선택 해제되어 보여야 합니다. |
| 4 | {save_action}<br>{reopen_action}<br>{tab_select_action} | {name}의 {second_value} 항목이 저장된 선택으로 보여야 합니다. |
| 5 | {name}의 선택을 기록한 원래 선택으로 복원<br>{save_action}<br>{reopen_action}<br>{tab_select_action} | {name}의 선택이 시험 전 값과 일치한다 |

## number-boundary

근거: TC-080

{name} 숫자 입력 경계값 (숫자 입력란)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name}에 승인된 최솟값 입력<br>입력 확정 | {name}에 승인된 최솟값이 보여야 합니다. |
| 3 | {name}에 승인된 최댓값 입력<br>입력 확정 | {name}에 승인된 최댓값이 보여야 합니다. |
| 4 | {name}의 입력값을 기록한 원래 값으로 복원<br>{cancel_action} | {close_expected_result} |
| 5 | {reopen_action}<br>{tab_select_action} | {name}의 값이 시험 전 값과 일치한다 |

## number-invalid

근거: TC-090

{name} 잘못된 숫자 입력 (숫자 입력란)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {name}에 {empty_value} 입력 시도<br>입력 확정 시도 | {name}의 {empty_value}에 대해 {empty_value_result}가 보여야 합니다. |
| 3 | {name}에 {non_numeric_value} 입력 시도<br>입력 확정 시도 | {name}의 {non_numeric_value}에 대해 {non_numeric_value_result}가 보여야 합니다. |
| 4 | {name}에 {below_minimum} 입력 시도<br>입력 확정 시도 | {name}의 {below_minimum}에 대해 {below_minimum_result}가 보여야 합니다. |
| 5 | {name}에 {above_maximum} 입력 시도<br>입력 확정 시도 | {name}의 {above_maximum}에 대해 {above_maximum_result}가 보여야 합니다. |
| 6 | {name}의 입력값을 기록한 원래 값으로 복원<br>{cancel_action} | {close_expected_result} |
| 7 | {reopen_action}<br>{tab_select_action} | {name}의 값이 시험 전 값과 일치한다 |

## button-save

근거: TC-230

{name} 버튼의 설정 저장 (버튼)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {setting_name}에서 {value} 선택 | {setting_name}에 {value}가 선택 상태로 보여야 합니다. |
| 3 | {save_action}<br>{reopen_action}<br>{tab_select_action} | {setting_name}에 {value}가 저장되어 보여야 합니다. |
| 4 | {setting_name}를 기록한 원래 선택으로 복원<br>{save_action}<br>{reopen_action}<br>{tab_select_action} | {setting_name}의 선택이 시험 전 값과 일치한다 |

## button-cancel

근거: TC-240

{name} 버튼의 설정 변경 취소 (버튼)

| No. | Steps |
|---|---|
| 1 | 설정값 복구 준비<br>원래 설정값과 복구 방법 기록 |

| No. | Steps | Expected Result |
|---|---|---|
| 1 | {path} | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |
| 2 | {setting_name}에서 {value} 선택 | {setting_name}에 {value}가 선택 상태로 보여야 합니다. |
| 3 | {cancel_action} | {close_expected_result} |
| 4 | {reopen_action}<br>{tab_select_action} | {setting_name}의 선택이 시험 전 값과 일치한다 |

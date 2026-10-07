"""Canonical TC wording dictionary extracted from structural TC rules."""

RULE_ID = "HPE990_TC_UP_DICTIONARY"
TITLE = "TC up dictionary: TC 문구 작성"
SOURCE = "cores/hpe990/rules/scenarios/tc_up_dictionary.py"
STATUS = "active"
BODY = r"""
# TC up dictionary

## 적용 범위와 관리

- TC 제목, 사전 조건, Steps, Expected Result 및 생성·검수 결과의 문구 작성 정본이다.
- TC 구조·ID·표 표시 규칙은 `cores/hpe990/rules/scenarios/tc_format.py`를 따른다.
  유형별 Step 구성은 `configs/ui_step_templates.json`에서 관리하며 본문을 복제하지 않는다.
- 표현 변경은 이 파일에 반영하고 적용 대상 생성기·템플릿·파생 문서가 일치하는지 확인한다.
  예시의 UI·시험값은 작성 예이며 실제 수집·시험 실행 또는 PASS 증거가 아니다.

## 입력유형 TC 제목

- 특정 입력요소의 선택·입력·버튼 동작을 검증하는 TC는 제목 끝에 `({입력유형})`을 붙인다.
  실제 수집 자료에서 확인한 유형명을 사용하고, TC ID에는 입력유형을 넣지 않는다.
- 유형 표기: 선택기는 `(선택기)`, 라디오 선택은 `(라디오 버튼)`, 체크 항목은 `(체크박스)`,
  숫자 필드는 `(숫자 입력)`, 버튼 동작은 `(버튼)`으로 표시한다.
  입력란의 세부 유형이 확인되지 않은 초안은 `(입력란)`으로 표시하고 확인 필요 상태를 유지한다.
  실제 유형 확인 후 제목·유형 태그를 구체화한다. 입력란이라는 이유만으로 숫자 입력으로 단정하지 않는다.
- 예: `Language 선택 및 저장값 확인 (선택기)`,
  `Beep Sound 선택 및 저장값 확인 (라디오 버튼)`,
  `Sleep Mode 체크 상태 변경 및 저장값 확인 (체크박스)`,
  `Wait (minutes) 숫자 입력 경계값 (숫자 입력)`, `Save 버튼의 설정 저장 (버튼)`.
- 화면 진입·스크롤 등 특정 입력유형 검증이 아닌 TC에는 유형을 붙이지 않는다.
  제목 변경 시 기존 ID를 유지하고 Gherkin·Markdown·HTML 제목을 같은 내용으로 반영한다.

## 사전 조건 문구

- 각 번호의 제목은 `Emulator 준비`, `키보드 연결`, `시험값 준비`처럼 준비 동작명으로 작성한다.
  Step에는 번호를, Steps에는 준비 항목 제목과 상세 절차·준비 상태를 함께 기재한다.
  제목 다음 줄부터 상세 절차를 들여쓰며 중간에 빈 줄을 넣지 않는다.
- 하나의 준비 항목에 여러 상세 절차가 있으면 한 번의 줄바꿈으로 이어 쓴다. 절차 사이에 빈 줄이나
  연속 줄바꿈을 넣지 않는다. Gherkin DocString 내부의 빈 줄과 Markdown 셀의 `<br><br>`도 금지한다.
  경로·파일명·SSID·입력값 등은
  해당 절차 아래에 한 단계 더 들여쓰고 `위치:`, `파일:`, `ssid:`처럼 식별 가능한 이름으로 작성한다.
  해당 TC에 실제로 필요한 정보만 적고 미확정 값은 확인 필요로 명시한다.

## Steps 문구

- 수행 절차는 `진입`, `클릭`, `선택`, `입력`, `확정`, `확인`, `스크롤`, `복원` 등
  동작명으로 끝낸다. `한다`, `된다`, `해야 한다`, `되어야 한다` 같은 문장 종결을 사용하지 않는다.
- 대상 경로·항목·값을 구체적으로 적고 기대 결과를 수행 절차에 섞지 않는다.
- 연속된 메뉴·탭 진입은 경로를 `>`로 연결하여 하나의 절차로 작성한다.
  경로의 실제 UI 명칭과 순서를 유지하고 마지막 대상의 동작으로 끝낸다.
  예: `Setup > Preferences > General 탭 선택`.
  Gherkin, Markdown TC 표, 검수 HTML에서 같은 경로 문구를 사용한다.
  입력·저장 등 별도 동작이나 중간 검증이 필요한 절차는 경로 표현으로 숨기지 않는다.
- 좋은 예: `Setup > Preferences > General 탭 선택`, `Beep Sound의 OFF 항목 선택`, `Save 클릭`.
- 수정 예:
  - `General 탭을 선택한다` → `General 탭 선택`
  - `Save를 누른다` → `Save 클릭`
  - `날짜 형식 항목 확인되어야 한다` → `날짜 형식 항목 확인`
  마지막 예시는 문구 변환 예시이며 General에 해당 항목이 존재한다는 의미가 아니다.

### 경로 통합 예시

수정 전 Steps:

```text
1. Setup 진입
2. Preferences 진입
3. General 탭 선택
```

수정 후 Steps:

```text
1. Setup > Preferences > General 탭 선택
```

수정 후 TC 표시:

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | Preferences 창의 General 탭과 설정 영역이 보여야 합니다. |

Gherkin에도 동일하게 `When Setup > Preferences > General 탭 선택`을 사용한다.
경로의 각 중간 화면을 개별 검증하는 TC는 해당 기대 결과가 있는 Step 묶음을 유지한다.

## Expected Result와 미확정 항목

- 화면·요소·값·선택 상태의 표시를 기대하는 문구는 `표시된다` 대신
  `보여야 합니다.`로 작성한다. `표시된다.`도 같은 표현으로 전환한다.
  이 규칙은 Expected Result에 적용하며 Steps의 동작명 종결 규칙은 유지한다.
- 문구 전환 예:
  - `General 설정 영역이 표시된다` → `General 설정 영역이 보여야 합니다.`
  - `Language에 English가 표시된다` → `Language에 English가 보여야 합니다.`
  - `OFF 항목이 선택 상태로 표시된다` → `OFF 항목이 선택 상태로 보여야 합니다.`
  열림·닫힘·저장·오류 등 별도 기대 동작의 의미를 표시 문구로 바꾸지 않는다.
- 각 묶음의 기대 결과는 관찰 가능한 화면·선택 상태·값·실제 기능 결과로 구체화한다.
  예: `Beep Sound의 OFF 항목이 선택 상태로 보여야 합니다.`
- Expected Result에는 문장형 표현을 사용할 수 있다. Steps의 동작명 종결 규칙과 구분한다.
- 입력 범위·오류 처리·지원 선택지가 확인되지 않았으면 `확인 필요`로 표시한다.
  실행용 TC로 확정하기 전 실제 입력값과 단일 기대 결과를 지정한다.
  `차단 또는 오류 또는 보정`처럼 여러 결과를 모두 허용하는 표현으로 통과를 판정하지 않는다.
- 작성 초안, 실행 가능, 실제 실행 결과를 구별한다. 작성·문법 검증을 테스트 PASS로 표시하지 않는다.

## 수집 요소 표시 목록

- 표시 목록의 기대 결과는 `하기 수집 요소가 각각 보여야 합니다.`로 시작하고,
  아래에는 항목명만 한 줄씩 작성한다. 항목마다 `항목이 표시된다`를 반복하지 않는다.
  예: `하기 수집 요소가 각각 보여야 합니다.` 다음 줄에 `Backup Date`, `Backup Filename`.

## TC 표시 예시

TC ID: TC-010
경로: Setup > Preferences > General
TC 제목: Beep Sound 선택 및 저장값 확인 (라디오 버튼)
사전 조건: 시험용 Edger 화면, 활성 RAM, 시험 전 선택과 복구 방법 기록.
다음 표는 작성 양식 예시이며 실행·통과 증거가 아니다.

| Step | Steps | Expected Result |
|---|---|---|
| 1 | 1. Setup > Preferences > General 탭 선택 | General 설정 영역이 보여야 합니다. |
| 2 | 1. Beep Sound의 OFF 항목 선택 | OFF 항목 선택, ON 항목 선택 해제 상태가 보여야 합니다. |
| 3 | 1. Beep Sound의 ON 항목 선택 | ON 항목 선택, OFF 항목 선택 해제 상태가 보여야 합니다. |
| 4 | 1. Save 클릭<br>2. Preferences 창이 열려 있으면 닫기 후 재진입<br>3. General 탭 선택 | 저장한 ON 항목이 선택 상태로 보여야 합니다. |
| 5 | 1. Beep Sound의 시험 전 선택 복원<br>2. Save 클릭<br>3. Preferences 창이 열려 있으면 닫기 후 재진입<br>4. General 탭 선택 | 시험 전 선택이 보여야 합니다. |

Preferences 창 닫기는 사전 조건에 넣지 않고 재진입 수행 Step에 명시한다.
창이 열려 있으면 닫은 후 재진입하고, 이미 닫혔으면 재진입만 수행한다.

## Gherkin 대응 예시

각 번호는 하나의 When/Then 묶음이다. When 뒤의 And는 수행 절차이고
Then 뒤의 And는 추가 기대 결과다. 수행 절차의 동작명 문구를 TC 표에서도 그대로 사용한다.

```gherkin
@draft @ISSUE-093ca349 @AC-preferences-general-input-types @path-Setup/Preferences/General
Feature: General 설정 확인
  @TC-010 @type-radio
  Scenario: TC-010 Beep Sound 선택 확인 (라디오 버튼)
    Given 시험용 Edger 화면이 표시되어 있다
    # Step 1
    When Setup > Preferences > General 탭 선택
    Then General 설정 영역이 보여야 합니다.
    # Step 2
    When Beep Sound의 OFF 항목 선택
    Then OFF 항목이 선택 상태로 보여야 합니다.
    And ON 항목이 선택 해제 상태로 보여야 합니다.
```
"""

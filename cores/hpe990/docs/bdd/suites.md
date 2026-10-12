# 검수 트리: Functions와 Basic Scenarios

각 제품 버전에는 기능 검수와 Tester 실행 흐름 두 가지 관점을 둡니다.

```text
HPE990 / 1.22
├─ Functions
│  ├─ TC-260 Edger / Job Manager — 화면 진입 및 시험 작업 목록 표시
│  ├─ TC-1690 Edger / Job Manager — 시험 작업 선택 및 미리보기
│  ├─ TC-270 Edger / Job Manager — 선택한 시험 작업 불러오기
│  └─ … 기존 화면 suite 경로를 포함한 TC 전체
└─ Basic Scenarios
   ├─ Job 불러오기
   │  ├─ TC-1920 시험 Job 불러오기와 편집 가능 상태 확인
   │  └─ 실행 순서의 정본 TC 링크
   └─ Job Manager 취소 흐름
      ├─ TC-1930 선택한 시험 Job을 불러오지 않고 나가기
      └─ 실행 순서의 정본 TC 링크
```

`Functions`는 명시적인 개별 기능 확인을 한 단계 TC 목록으로 제공합니다. 각 항목은
`TC-ID 화면 suite 경로 — 제목` 형식으로 표시합니다. Job 시나리오 경로는
`Basic Scenarios > Job > Scenario`로 표시하며,
각 Job Scenario는 TC ID를 발급한 Gherkin 정본으로 작성하고, 다른 TC와 같은 Pre-condition 및
`No. | Steps | Expected Result` 표를 사용합니다. `cores/hpe990/configs/basic_scenarios.json`은
Job별 분류, 시나리오 TC ID, 수행 순서 및 관련 TC를 연결합니다.
TC-250, TC-280, TC-1740은 Job 흐름의 기준·결과 검증이므로 `basic_only`로 표시해 Functions에서
제외하고 각 Job의 순서 단계로 둡니다. Basic Scenarios의 TC 링크에서 검증 상세로 이동할 수 있고,
TC 본문에는 Basic Scenario로 돌아가는 추가 문구나 링크를 넣지 않습니다.

Function TC는 기능 하나를 독립 검증할 수 있도록 자체 사전조건과 기대 결과를 가집니다.
Job 단위 TC는 Tester가 순서대로 수행할 흐름과 전후 상태를 표로 포함합니다. Job 내부 TC의
순서는 실제 수행 순서입니다. Function 트리의 화면 순서는 탐색 분류입니다.

현재 Job 흐름은 관찰된 TC를 연결한 검수 초안입니다. Function TC 상세는 독립 실행을 위한 준비를
포함하므로 연속 상태를 요구하는 Basic Scenario와 실행 절차가 다를 수 있습니다. 두 흐름의 공유
상태·복귀 조건을 확정하기 전에는 연결만으로 Basic Scenario 실행 완료로 간주하지 않습니다.
작성된 시나리오는 초안으로, 이 변경에서 자동화 시험을 실행한 결과가 아닙니다.

[공유 검수 웹](http://172.20.13.185:9999/tc-up-validation/)은 TC 파일과 경로 변경을
서버 재시작 없이 반영합니다. 파일의 Suite 경로와 실제 Steps의 조작 경로를 구분합니다.

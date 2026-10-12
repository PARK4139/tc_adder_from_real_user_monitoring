"""Canonical screen and functional grouping of review suites."""

RULE_ID = "HPE990_TC_SUITE_HIERARCHY"
TITLE = "검수 TC의 화면·기능 혼합 Suite"
SOURCE = "cores/hpe990/rules/scenarios/suite_hierarchy.py"
STATUS = "active"
BODY = r"""
# Functions와 Basic Scenarios의 양방향 검수 트리

- 제품 버전 아래 두 개의 최상위 노드를 제공한다: `Functions`와 `Basic Scenarios`.
  `Basic Scenarios`는 Job 기반 Tester 수행 시나리오를 담는다.
  HPE990 1.22의 기존 화면·탭 TC 트리는 기본적으로 `Functions` 아래에 보존하되,
  Job 흐름 전체의 기준·결과 확인 TC는 `Basic` 전용으로 분류한다.
- `Functions`는 명시적인 독립 기능 검증을 제공한다. 기존 UI 경로와 명칭을 유지하며,
  Edger > Setup > Preferences > General 같은 실제 화면 계층으로 탐색한다.
  기능 TC는 하나의 검증 목적을 가지며 자체 Setup과 기대 결과를 포함한다.
- `Basic Scenarios`는 Tester가 수행하는 Job 흐름을 제공한다. 각 Job은 실행 순서,
  Job별 Setup, 필요한 TC 참조, 종료 상태와 결과를 기술한다.
  순서는 Tester가 따를 순서이며 앞 단계의 실패·미수행은 후속 단계 실행에 영향을 준다.
- 한쪽 관점의 TC 본문을 다른 쪽에 복사하지 않는다. Basic Scenario의 각 단계는 정본
  TC ID를 참조한다. TC 본문에는 Basic Scenario로 돌아가는 추가 문구나 링크를 넣지 않는다.
  두 관점은 같은 검증 정본을 사용하며 독립적인 결과를 만들어내지 않는다.
- Job Setup은 그 Job을 독립적으로 시작하는 데 필요한 데이터를 명시한다. 시험 Job 식별자,
  기대 속성, 기존 사용자 데이터 보호, 시작 화면, 종료·복구 상태를 포함한다.
  Function TC 자체의 사전조건은 기능 단독 검증에 계속 사용한다.
- TC의 순차 실행이 상태를 공유한다면 이를 Basic Scenario의 단계와 상태 전이로 명시한다.
  각 Function TC의 독립 실행 경로와 Basic Scenario의 연속 실행 경로를 혼동하지 않는다.
- 여러 화면에 걸친 기준·전후 상태나 Job 결과를 확인하는 TC는 Basic에 둘 수 있다.
  이 항목은 `basic_only`로 표시해 Functions에서 제외하되, Job의 순서 있는 TC 단계로 유지한다.
- 화면·기능 기준 순서는 Functions 내부에 적용하고, Tester 진행 순서는 Basic Scenarios
  내부 Job 및 단계에 적용한다. 한 트리의 정렬 순서를 다른 관점의 순서로 해석하지 않는다.
- Job을 포괄하는 Basic Scenario도 일반 TC다. `@TC-...` Gherkin 정본, ID 발급 기록,
  TC별 Pre-condition 및 번호별 Steps / Expected Result 표를 사용한다. 별도 `BS-...` 식별자는
  사용하지 않는다. configs/basic_scenarios.json은 Job 분류, 제목, 실행 순서 TC 참조,
  `basic_only` 표시만 관리하며 Setup과 시험 본문을 복제하지 않는다.
- 제목과 Steps는 실제로 관찰된 UI 명칭·조작을 사용한다. 미관찰 동작이나 미확정 값은
  구현 완료처럼 표현하지 않는다. ID, 태그, wording은 관련 canonical rules를 따른다.
"""

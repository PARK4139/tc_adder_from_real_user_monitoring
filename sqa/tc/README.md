# 검수 TC 파일 관리

TC 정본은 상태 폴더 아래의 개별 UTF-8 Gherkin 파일입니다.
`to_review/`는 검수 대기, `reviewed/`는 검수 완료입니다.
TC 파일을 반대 폴더의 같은 상대 경로로 이동하면 상태가 변경됩니다.
ID와 본문은 유지하고 복사본이나 별도 상태 필드를 만들지 않습니다.

예: `to_review/setup/preferences/general/TC-030.feature`를
`reviewed/setup/preferences/general/TC-030.feature`로 이동하면 검수 완료입니다.

- 파일당 단일 Feature와 Scenario를 작성합니다. 파일명과 `@TC-030` 태그를 일치시킵니다.
- `@path-Edger/Setup/Preferences/General`로 트리 경로를 지정합니다. HPE990 1.22의 메인 화면은 Edger이며 Setup은 그 하위입니다.
- 화면·기능 혼합 분류는 [Suite 구성](../../cores/hpe990/docs/bdd/suites.md)을 따릅니다. 기능 분류명은 실제 Steps의 메뉴명이 아닙니다.
- 제목, 사전조건, Steps, Expected Result는 해당 파일에서 수정합니다.
- 신규 TC ID는 `cores/hpe990/configs/tc_ids.json`과 TC 발급 규칙을 따릅니다.
- 표시 순서는 `cores/hpe990/configs/tc_review.json`의 `order`에서 관리합니다. 신규 파일은 자동 발견되며
  목록에 없는 ID는 기존 순서 뒤에 숫자순으로 표시합니다.
- 검수 웹은 두 상태 폴더의 수정·추가·이동·삭제를 재시작 없이 감지합니다. 문법 오류나 중복 ID가 있으면 마지막 정상 화면을
  유지하므로 파일을 수정해야 반영됩니다.
- TC-010 수집 목록은 자동 갱신 영역이며 다른 TC 본문을 변경하지 않습니다.
- `reviewed/`의 TC와 부속 문서는 자동 갱신에서 보호됩니다. 건너뛴 이유는 수집 결과의
  `tc_sync.reason`에서 확인합니다. `to_review/`로 이동하면 다음 수집부터 자동 갱신이 재개됩니다.

검수 완료 상태도 실행용 BDD 등록이나 PASS 증거가 아닙니다.
공유 주소: http://172.20.13.185:9999/tc-up-validation/

정적 HTML 생성: `uv run python -m cores.hpe990.scripts.render_tc_review`.
작성 규칙은 `cores/hpe990/rules/scenarios/`의 `tc_format.py`, `tc_up_dictionary.py`,
`suite_hierarchy.py`, `review_state.py`를 따릅니다.

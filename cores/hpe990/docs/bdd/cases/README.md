# 검수 TC 파일 관리

TC 정본은 화면 경로 아래의 개별 UTF-8 Gherkin 파일입니다.

예: `setup/preferences/general/TC-030.feature` (Language).

- 파일당 단일 Feature와 Scenario를 작성합니다. 파일명과 `@TC-030` 태그를 일치시킵니다.
- `@path-Setup/Preferences/General`로 트리 경로를 지정합니다.
- 제목, 사전조건, Steps, Expected Result는 해당 파일에서 수정합니다.
- 신규 TC ID는 `configs/tc_ids.json`과 TC 발급 규칙을 따릅니다.
- 표시 순서는 `configs/tc_review.json`의 `order`에서 관리합니다. 신규 파일은 자동 발견되며
  목록에 없는 ID는 기존 순서 뒤에 숫자순으로 표시합니다.
- 검수 웹은 수정·추가·삭제를 감지합니다. 문법 오류나 중복 ID가 있으면 마지막 정상 화면을
  유지하므로 파일을 수정해야 반영됩니다.
- TC-010 수집 목록은 자동 갱신 영역이며 다른 TC 본문을 변경하지 않습니다.

개별 파일은 검수 초안입니다. 실행용 BDD 등록이나 PASS 증거가 아닙니다.
공유 주소: http://172.20.13.185:9999/tc-up-validation/

정적 HTML 생성: `uv run python -m cores.hpe990.scripts.render_tc_review`.
작성 양식과 문구는 `rules/scenarios/tc_format.py`, `tc_up_dictionary.py`를 따릅니다.

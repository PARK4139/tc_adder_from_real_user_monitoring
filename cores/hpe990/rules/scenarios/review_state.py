"""Folder authority for TC review state."""

RULE_ID = "HPE990_TC_REVIEW_STATE"
TITLE = "TC 검수 상태는 폴더로 관리"
SOURCE = "cores/hpe990/rules/scenarios/review_state.py"
STATUS = "active"
BODY = r"""
# TC 검수 상태는 폴더로 관리

- 저장소 루트의 `sqa/tc/to_review/`는 검수 대기, `sqa/tc/reviewed/`는 검수 완료다.
- 상태의 정본은 파일 위치다. 별도 JSON 상태, 본문 상태 또는 수동 `@review` 태그를 저장하지 않는다.
- 상태를 바꿀 때는 개별 TC 파일 하나를 반대 상태 폴더로 이동한다. ID, Suite 경로, 본문은 유지한다.
- 예를 들어 `sqa/tc/to_review/setup/preferences/general/TC-030.feature`를
  `sqa/tc/reviewed/setup/preferences/general/TC-030.feature`로 옮기면 검수 완료다.
  원래 위치로 옮기면 다시 검수 대기다. 파일을 복사해 양쪽에 중복 보관하지 않는다.
- 검수 화면은 두 상태 폴더를 함께 조회하고 파일 위치에 따라 상태를 동적으로 표시한다.
  검수 대기인 TC에는 기본 상태 칩을 표시하지 않는다. 검수 완료인 TC에만
  `검수 완료` 칩을 표시하며, 검수 상태 칩이 없으면 검수 대기로 해석한다.
  카드와 트리에서 같은 표시 규칙을 적용한다.
- TC 파일의 추가, 수정, 이동, 삭제는 서버 재시작 없이 검수 화면에 반영한다.
  Suite 구조와 실행 결과는 검수 상태와 별개다.
- 수집 결과에 따른 TC 자동 갱신은 `to_review/`에서만 수행한다. `reviewed/`의 TC와
  부속 문서는 자동 변경하지 않고 건너뛴 이유를 기록한다. 자동으로 검수 대기 상태로
  되돌리지 않는다.
- 예를 들어 검수 완료 TC-010은 새 UI가 수집되어도 유지한다. 파일을 `to_review/`로
  옮긴 뒤 다음 자동 갱신에서 수집 요소를 반영한다. 직접 지정한 경로에도 같은 보호 규칙을 적용한다.
"""

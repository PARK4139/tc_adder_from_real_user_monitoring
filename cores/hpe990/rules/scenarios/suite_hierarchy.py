"""Canonical screen and functional grouping of review suites."""

RULE_ID = "HPE990_TC_SUITE_HIERARCHY"
TITLE = "검수 TC의 화면·기능 혼합 Suite"
SOURCE = "cores/hpe990/rules/scenarios/suite_hierarchy.py"
STATUS = "active"
BODY = r"""
# 화면·기능 혼합 Suite

- 상위 Suite는 실제 화면·탭 이름과 기존 경로를 유지한다. 실제 UI 명칭은 임의로
  번역하거나 약자로 줄이지 않는다. Edger가 메인 화면인 HPE990 1.22에서는
  Setup을 Edger 하위에 둔다. 예: Edger > Setup > Preferences > General.
- 같은 기능을 검증하는 TC가 여러 개이면 해당 화면 아래에 기능 Suite로 묶는다.
  여러 화면에 걸친 연속 흐름도 기능 묶음 아래 실제 화면을 배치할 수 있다.
  기능 묶음은 검수 분류이며 실제 메뉴·화면이 존재한다고 설명하지 않는다.
- 단일 TC만 있는 기능은 가장 가까운 화면 또는 기능 묶음에 바로 배치한다.
  초기 상태·선택·저장·복귀 같은 검증 단계마다 단일 TC 폴더를 만들지 않는다.
- 실제 화면과 기능을 혼합해도 같은 TC는 한 경로에만 둔다. Suite 이동으로
  TC를 복제하거나 재번호하지 않는다. ID 발급과 경로 태그 형식은 tc_format.py를 따른다.
- Suite는 검수 탐색 구조이고 Steps는 실제 조작 경로다. 기능 분류명을 실제 UI 클릭
  대상으로 Steps에 넣지 않는다. 생성·템플릿 소비자도 이 두 경로를 구분한다.
- 검수 정본 경로는 개별 TC의 @path 태그로 관리한다. 독립적인 Suite 제목·TC 사본
  카탈로그를 만들지 않으며 HTML 트리는 해당 태그에서 생성한다.

예시:

```text
Edger > Setup > Preferences > General
  Sleep Mode             # 체크 및 Wait 입력·경계값·오류 TC 묶음
  Message Box Font Size  # 입력·경계값·오류 TC 묶음
  TC-030 Language 설정 및 적용 확인 (선택기)  # 단일 TC는 바로 배치
Edger > 작업 불러오기
  TC-250 작업 미선택 상태의 UI 확인
  Job Manager
    TC-260 Job Manager 진입 및 설치 샘플 목록 확인
    TC-270 CIRCLE 샘플 선택 및 작업 불러오기
  TC-280 작업 불러오기 후 UI 활성화 확인
```

예시의 기능 묶음은 검수용이며 Steps에는 `Edger의 폴더 버튼 클릭`처럼 실제 화면에서
관찰된 대상을 사용한다. 미래 화면은 TC 근거가 확보될 때 추가하고 빈 Suite는 표시하지 않는다.
"""

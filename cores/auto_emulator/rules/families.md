# families — auto_emulator

| function family | meaning | implementation location |
|---|---|---|
| bdd | HPE990을 실행 대상으로 사용하는 auto_emulator 도구 검증: Real Activity Monitoring, 텔레메트리, 분석, 흐름, 제어 실패, 조회, 드래그, OCR·키보드 입력 | `cores/auto_emulator/tests/bdd/`, `cores/auto_emulator/configs/one_shot_bdd.json` |
| diagnostics | 도구 검증 BDD의 등록·바인딩·데스크톱 입력 승인 검사 | `cores/auto_emulator/tests/test_bdd_registry.py` |

HPE990 제품 기능 TC는 `sqa/tc/`에서 관리한다. 기존 이슈 태그는 원래 UUID와 이슈 위치를 유지한다.

# 버전별 UI ID MAP

공통 의미 ID와 버전별 native 선택자, 현재 세션의 UI ID/HWND를 구분합니다.
정본은 `configs/ui_semantics.json`이며 실제 관찰·확인 기록은 기존
`{D_TEMP}/hpe990/runtime/ui-elements.sqlite3`의 `ui_map_*` 테이블에 저장합니다.

## MCP 사용

1. `hpe990_ui_map(session_id)`으로 현재 버전과 후보를 수집합니다.
2. 이름·화면·부모 경로를 확인하고 `action="verify"`, `semantic_id`, 후보의 `ui_id`를 전달합니다.
3. `hpe990_ui_resolve(session_id, semantic_id)`으로 현재 대상을 해석합니다.
4. `hpe990_ui_control_semantic(session_id, semantic_id)`으로 조작합니다.
5. 적용 결과는 별도로 확인합니다. 매핑 확인이나 입력 전달은 기능 PASS가 아닙니다.

`action="catalog"`는 버전과 확인 기록을 조회하며 `include_observations=true`로
버전별 최신 수집의 모든 native 이름·경로·ID를 볼 수 있습니다.
`action="revoke"`와 의미 ID를 전달하면 현재 버전의 확인을 해제합니다.
일반 MCP UI 수집도 native 매핑 관찰을 기록합니다. 버전 식별 실패는 `ui_map_error`로 남습니다.

## 다른 버전 대응

실행 파일 SHA-256을 버전 구분 키로 사용하며 PE FileVersion/ProductVersion도 보관합니다.
PE 값이 없으면 미확정으로 남깁니다. 이름이 같더라도 새 해시는 별도 확인이 필요합니다.
TC는 공통 의미 ID를 유지합니다. 내부 이름이 달라진 버전은 해당 정의에 다음처럼 추가합니다.

```json
"variants": {
  "HPE990:<실제 실행 파일 SHA-256>": {
    "internal_name": "<새 버전에서 관찰한 내부 이름>",
    "ancestor_names": ["<관찰한 부모 이름>"]
  }
}
```

변경할 수 있는 선택자 필드는 `internal_name`, `ancestor_names`, `root_names`, `class_name`입니다.
이후 새 버전에서 실제 후보를 수집하고 확인해야 합니다. 정의 변경 시 이전 확인을 재사용하지 않습니다.
검증된 루트 별칭은 Preferences/환경 설정처럼 명시적으로 관리합니다.
내부 이름이 Qt objectName이라는 주장이나 COMBO 이름만으로 실제 유형이 검증됐다는 주장은 하지 않습니다.

초기 공통 의미 정의는 Preferences, General, Language, Save, Cancel 5개입니다.
모든 수집 native 요소의 원래 이름과 ID는 저장하지만 모든 요소의 의미가 확정된 것은 아닙니다.
실제 다른 Emulator 버전의 실행 검증은 해당 버전 설치 후 진행해야 합니다.
배포 EXE와 기존 BDD 실행 등록은 이번 변경으로 갱신하지 않습니다.

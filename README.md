# auto_emulator

HPE990 PC Emulator를 MCP로 실행·관찰·제어합니다. Python은 uv로 관리하고,
지속 창 이벤트·계층·화면 해시 수집은 Rust로 구현합니다.

## 실행

배포 위치는 **`auto_emulator/auto_emulator_X.Y.exe`**, 고정 실행 파일은 `auto_emulator.exe`입니다.
정식 버전과 SHA256은 `cores/hpe990/configs/releases.json`의 `released` 기록을 확인하세요.
Python을 별도로 설치하지 않아도 배포 EXE의 MCP 서버와 내장 BDD 실행기를 사용할 수 있습니다.
HPE990 설치, Explorer 및 Windows 대화형 데스크톱은 필요합니다.

```powershell
.\auto_emulator.exe
.\auto_emulator.exe status
.\auto_emulator.exe --mcp
```

기본 실행 범위는 **HPE990 실행 → Continue 클릭 → Edger 확인**이며 RAM도 자동으로 시작합니다.
대상은 공용 시작 메뉴의 `Huvitz_pc/HPE990/HPE990.lnk`로 고정되어 있습니다.
Qt의 `QT_USE_NATIVE_WINDOWS=1`을 실행 자식에 적용해 컨트롤을 식별합니다.
반복 실행은 동일 세션을 재사용합니다. Explorer가 실행한 별도 도우미 덕분에 MCP 연결 종료 후에도
앱과 RAM이 유지됩니다. `session_id`는 실행 결과에서 확인하세요.

## MCP 도구

| 기능 | 도구 |
|---|---|
| 실행 / 상태 / 정상 종료 요청 / 명시적 앱 종료 | `hpe990_launch`, `hpe990_status`, `hpe990_close`, `hpe990_stop` |
| RAM 시작 / 상태 / 정리 | `hpe990_ram_start`, `hpe990_ram_status`, `hpe990_ram_stop` |
| 창·모달·컨트롤·스크린샷 / 수집 목록 | `hpe990_ui_collect`, `hpe990_ui_catalog` |
| BDD 시나리오 화면 / 뷰어 서버 정리 | `hpe990_ui_visualize`, `hpe990_ui_viewer_stop` |
| 식별한 컨트롤 입력 / 창 이동·크기 | `hpe990_ui_control`, `hpe990_window_geometry` |
| 로컬 이벤트 읽기 / 검증·내보내기 | `hpe990_telemetry_read`, `hpe990_telemetry_export` |
| 상태·전이 분석 / 시나리오·추적표 / 실제 BDD 실행 | `hpe990_ui_analyze`, `hpe990_bdd_catalog`, `hpe990_bdd_run` |

컨트롤은 현재 세션의 이름·HWND·부모 창으로 지정합니다. 중복 이름은 `root_hwnd` 또는 `hwnd`로
구분하고, 화면 좌표 대신 필요시 컨트롤 내부 `point_fraction`을 사용합니다. 모든 입력 전후에
RAM 승인 기록과 화면 증거를 남깁니다. 텍스트 원문은 제어 로그에 저장하지 않습니다.

`hpe990_bdd_run`의 `allow_desktop_input: true`는 실제 앱을 실행·제어·종료합니다.
외부에서 실행한 세션의 종료는 거부합니다. Edger는 WM_CLOSE를 무시하므로 `hpe990_close`가
`closed: false`를 반환할 수 있습니다. `hpe990_stop`의 **명시적 `force: true`**는 소유한 HPE990
프로세스만 종료하며 `exit_method: explicit_force`로 기록합니다. 시스템 Shutdown 확인창은
테스트에서 취소하며 Windows 종료 성공으로 보고하지 않습니다.

루트 `.mcp.json`은 uv 소스 서버 설정입니다. uv가 PATH에 없으면 클라이언트에서 실행 파일 경로를
지정하세요. 배포 EXE를 연결하려면 `auto_emulator.exe`의 절대 경로와 `--mcp` 인자를 사용하세요.

## 개발·검증·one shot

TC 작성 규칙과 예시는 [tc_format.py](cores/hpe990/rules/scenarios/tc_format.py)의 `BODY`를
따릅니다. General TC 작성 결과는 [preferences_general.md](cores/hpe990/docs/bdd/preferences_general.md)에서 확인합니다.
`uv run python -m cores.hpe990.scripts.render_tc_review`는 같은 Gherkin 초안으로
`{D_TEMP}/hpe990/evidence/093ca349/preferences-general-tc-review.html`을 생성합니다.
TC별 Step / Steps / Expected Result 표와 입력 즉시 반영되는 퍼지 검색을 제공합니다.
TC ID·제목·Steps·Expected Result를 검색하며 공백으로 구분한 검색어는 모두 일치해야 합니다.
예: `lng`는 Language, `beep off`는 Beep Sound의 OFF 관련 TC를 조회합니다.
관련도 순으로 정렬하며 검색창에서 ↑/↓로 선택하고 Enter로 해당 TC에 이동합니다.
좌측 목록은 경로 → 입력유형 → 입력요소 → TC 트리로 표시하며 같은 요소의 여러 TC를 묶습니다.
그룹별 개수와 접기·펼치기를 제공하고, TC 제목 아래 `TC-022` 형식의 ID를 표시합니다.
TC ID는 경로와 독립적으로 관리하며 Gherkin의 `@path-Setup/Preferences/General` 태그가 트리 경로를 지정합니다.
검색 시 일치하는 가지를 펼쳐 검색어를 강조하고, 선택 항목을 강조합니다.
미확정 사항은 `지원 언어 미확정`, `최소·최대값 미확정`, `입력유형 미확정` 등의 구체적인 칩으로 표시합니다.
칩은 Gherkin의 `@spec-*` 태그에서 생성하며 좌측 트리와 TC 제목 우측에 동일하게 표시합니다.
검색 초기화·인쇄/PDF 버튼은 제공하지 않습니다. 초안 변경 후 다시 생성합니다.
같은 망에 공유할 때는 `uv run python -m cores.hpe990.scripts.share_tc_review --bind <LAN-IP> --port 9999`를
사용합니다. 생성한 HTML 한 파일만 `/tc-up-validation/`에서 제공하며 폴더 목록·다른 파일은 제공하지 않습니다.
주소는 `{D_TEMP}/hpe990/runtime/tc-review-share.json`에 기록됩니다. 접속 허용은 해당 IP·포트·같은 서브넷으로
방화벽을 제한합니다. 현재 허용 규칙은 Private 프로필의 TCP 9999이며 로컬 주소는
`172.20.13.185`, 접속 허용 주소는 `172.20.0.0/20`입니다. uv 실행 경로 별칭에 따른
프로그램 필터 불일치를 피하도록 프로그램 대신 해당 IP·포트·접속 주소로 제한합니다.
TC 원본을 100ms 간격으로 감시하고 SSE로 변경을 전달하여 서버 재시작 없이
열린 화면을 자동 갱신합니다. 검색어와 스크롤 위치는 유지합니다. 추가 공유 경로가 필요하면
`--token <토큰 또는 경로 이름>`을 지정합니다. 경로 이름은 영문 소문자·숫자·하이픈으로 구성합니다.
공유 주소는 `http://172.20.13.185:9999/tc-up-validation/`으로 고정됩니다.
`--token`을 생략하거나 과거 토큰으로 재실행해도 `/tc-up-validation/`과 실시간 갱신 경로를 제공합니다.
종료는 `uv run python -m cores.hpe990.scripts.share_tc_review --stop`입니다.
Windows에서 내 PC만 접속되고 팀원 PC는 시간 초과가 발생하면 서버 실행 파일에 대한
인바운드 차단 규칙도 확인합니다. 차단 규칙은 포트 허용 규칙보다 우선합니다.
이 PC의 `pythonw.exe`에는 차단 규칙이 있으므로 공유 서버는 uv 환경의 `python.exe`로 실행합니다.
현재 허용 범위는 Private 프로필, TCP 9999, 로컬 `172.20.13.185`, 원격 `172.20.0.0/20`입니다.

### HWND 외 입력요소 보완 수집

`hpe990_ui_collect`는 기존 `nodes`의 HWND 트리를 유지하고, `accessibility`와 `visual`을 추가합니다.
접근성 백엔드는 `msaa`(기본), `uia`, `none` 중 선택하며 별도 프로세스에서 3초로 제한합니다.
응답 없는 접근성 제공자는 오류로 기록하고, 캡처 기반 OCR·입력란 테두리 수집을 계속합니다.
Windows OCR는 설치된 언어를 사용하며 인식 원문을 보존합니다. 영문 철자가 오인식될 수 있습니다.
Rust가 PNG 테두리 탐색과 OCR용 확대를 처리합니다. 소스 실행 전 빌드:

`cargo build --release --manifest-path cores/hpe990/rust/visual/Cargo.toml --target-dir "$env:USERPROFILE/Desktop/Temp/hpe990/build/visual"`

시각 후보는 `root_hwnd`, 원본 PNG/해시, 이미지 기준 좌표를 가지며 child HWND를 만들지 않습니다.
편집 가능·읽기 전용·값은 미검증 상태로 남깁니다. `screenshots=false`이면 시각 수집도 생략합니다.
`hpe990_ui_catalog`의 `supplemental_elements`에서 추가 결과와 스냅샷을 조회할 수 있습니다.
`hpe990_ui_control`의 `scroll_down`/`scroll_up`은 관찰된 `qt_scrollarea_viewport`만 대상으로 합니다.
RAM은 계속 작동합니다. 이 보완은 소스 MCP용이며 배포 EXE 0.5는 갱신하지 않았습니다.

### BDD 시나리오 전용 화면

`hpe990_ui_visualize`는 기존 `{D_TEMP}/hpe990/evidence/inspection/ui-gallery.html` 위치에
BDD 시나리오 전용 화면을 생성합니다. UI 갤러리·이미지·컨트롤 트리는 표시하지 않습니다.
현재 uv 소스 MCP에서 제공하며 배포 EXE 0.5에는 포함되지 않습니다.
Emulator 실행이나 UI 수집 없이 목록을 조회할 수 있습니다. 시나리오 이름·이슈·단계를
검색하고, 항목을 선택하면 Given/When/Then 원문과 pytest 바인딩을 확인합니다.
등록 변경과 등록 오류는 반환된 `url`에서 3초마다 반영됩니다. `html` 파일은 저장 시점 목록입니다.
등록 여부는 테스트 통과를 뜻하지 않습니다. `session_id`는 목록 필터에 사용하지 않습니다.
MCP 연결 종료 후에도 서버가 유지되며 `hpe990_ui_viewer_stop`으로 정리합니다.

```powershell
uv sync --locked
uv run ruff check cores
uv run ruff format --check cores
uv run python -m pytest --ignore=cores/hpe990/tests/bdd
uv run python -m pytest cores/hpe990/tests/bdd --allow-desktop-input
.\cores\hpe990\scripts\one-shot-pipeline.cmd --allow-desktop-input
```

uv가 PATH에 없으면 `UV_EXE`에 설치된 uv.exe를 지정합니다. Rust 빌드는 Cargo와 Windows
링커가 필요합니다. 공통 one-shot 콘솔을 재사용하고 실제 작업의 종료 코드를 반환합니다.
Rust/lint/일반 테스트 → 등록된 실제 BDD → 버전 예약·빌드 → 후보·배포·고정 EXE의 MCP 및 BDD
검증을 모두 통과해야 배포합니다. EXE 내장 실행기도 검증합니다. 누락·중복 바인딩, 0개 테스트,
skip/xfail/실패는 통과로 인정하지 않습니다. 실패한 버전 번호는 재사용하지 않습니다.

중간 빌드는 `{D_TEMP}/hpe990/build/`, 증거는 `{D_TEMP}/hpe990/evidence/{issue-id}/`,
실행 상태는 `{D_TEMP}/hpe990/runtime/`에 저장합니다. D_TEMP는 실제 Windows Desktop/Temp입니다.
BDD의 JUnit, MCP 계약, 화면, 분석, 제어와 RAM 동시 실행 보고서를 해당 이슈 증거에서 확인하세요.

## 관찰 범위

### UI 요소 ID와 SSOT

수집된 모든 HWND·접근성·시각 요소에는 `ui_id`(`UI-000001` 형식)를 부여합니다.
중앙 원장은 `{D_TEMP}/hpe990/runtime/ui-elements.sqlite3`이며, SQLite 트랜잭션으로
ID 중복 발급을 방지합니다. TC ID와 별도로 관리하고 번호를 재사용하지 않습니다.
`hpe990_ui_collect`와 `hpe990_ui_catalog`의 `ui_registry`에서 정의를 조회합니다.
원본 HWND·provider `id`·PNG는 출처 증거로 보존하며, 명확하게 일치한 native/visual
요소는 같은 내부 ID를 사용합니다. `parent_ui_id`와 `root_ui_id`로 계층을 연결합니다.

`identity_scope=semantic_path`는 이름과 조상 경로가 모두 유일한 요소입니다.
위치·HWND·세션이 바뀌어도 경로가 같으면 ID를 유지합니다. 이름 없는 요소,
중복 경로와 연결되지 않은 OCR 요소는 `session_observation`으로 구분하며,
재생성·HWND 재사용 시 동일성을 보장하지 않습니다. 과거 수집 파일은 수정하지 않고
카탈로그에서 원장에 연결합니다. 원장 파일도 증거와 함께 백업해야 ID 연속성이 유지됩니다.
정본 규칙은 `cores/hpe990/rules/ui_identity.py`입니다.

Telemetry는 `schema_version`, `session_id`, `run_id`, `sequence`로 연결한 로컬 JSONL입니다.
원격 전송은 후속 범위입니다. WinEvent와 주기적인 HWND 상태·RGB 해시를 함께 사용하며 실제
수집 간격·스캔 시간·이벤트 지연을 보고합니다. 화면 가림이나 샘플 사이의 미보고 순간 변화는
완전 검출을 보장하지 않습니다.

수집 목록은 **관찰한 UI**와 **미탐색 경로**를 분리합니다. 유지보수 코드가 필요한 영역을 포함한
전체 UI 수집은 아직 완료되지 않았습니다. 수집한 모든 컨트롤의 도구 매핑이 실제 모든 기능의
성공 검증을 의미하지 않으며, 미탐색 기능을 완료로 표시하지 않습니다.

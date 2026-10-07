# 구현 및 검증 결과

## 배포

- 실행 파일: `auto_emulator/auto_emulator_0.5.exe` (29,458,052 bytes).
- 고정 실행 파일: `auto_emulator/auto_emulator.exe`; 동일 SHA256 확인.
- SHA256: `a7560e99f9a1e89f1e4ab6181deee48e24dce6fdb0dd7cda5f5a8c927773f325`.
- one-shot 실행: `20261006T104509Z-239228b0`.
- 증거: `{D_TEMP}/hpe990/evidence/5488b646/20261006T104509Z-239228b0/pipeline-report.json`.

## 완료된 이슈

| 이슈 | 결과 |
|---|---|
| c35e84d2 | 실행 → Continue → Edger |
| 92dd1b63 | Rust WinEvent·창 계층 RAM, 관찰 지점·세션 연결 검증 |
| 4c1abd34 | 로컬 telemetry, 화면 해시·순서·스키마·제어 연결 검증 |
| f797f6a4 | 관찰한 상태·전이와 MCP 도구 매핑 분석 |
| 093ca349 | 필수 실행~종료 흐름의 Gherkin 및 분석 추적표 |
| 5488b646 | MCP를 통한 실제 BDD 자동제어, 제어 실패 기록·RAM 정리 |

안전/등록 검증 17개와 필수 BDD 5개가 통과했다. 소스·후보·배포·고정 실행 파일의
BDD 및 세 EXE의 내장 BDD를 합해 실제 시나리오 실행 35건이 모두 통과했다.
각 EXE의 공개 MCP 도구 16개를 실제 호출로 검증했다. RAM 연결 누락 0건이며 앱 종료 후
모니터 정리를 확인했다. 종료는 명시적인 소유 프로세스 종료이며, 정상 시스템 종료로
보고하지 않는다.

## 미완료

`50c688e3` 전체 UI 수집은 blocked이다. 설정 9개 경로에서 native 컨트롤 1,816개를
수집했고 미탐색 컨트롤 87개를 명시했다. 배포 EXE에서도 Maintenance Code 화면의
앱 제공 입력값을 그대로 제출했지만 Setup으로 돌아왔고 유지보수 영역은 열리지 않았다.
접근 절차가 확인되면 남은 경로를 탐색하고 전체성을 검증한다.

재확인 증거: `{D_TEMP}/hpe990/evidence/inspection/maintenance-audit-*.json`.
모든 기능의 전체 검증이나 미탐색 UI의 수집 완료를 주장하지 않는다.
화면 가림과 샘플 사이 미보고 변화의 검출 한계는 README에 기록했다.

## 마지막 실행 상태

2026-10-07 추가 탐색에서 Job Manager 5개 탭, 내장 CIRCLE 샘플 불러오기,
Job Editor 및 Left - Size 숫자 입력 창을 수집했다. 숫자 입력을 원래 0으로
복원한 뒤 Editor Cancel로 Edger에 돌아왔고, 자동제어 중 RAM 활성 상태를 확인했다.
작업 데이터가 없어 탐색할 수 없다는 이전 가정은 내장 샘플 확인으로 해소했다.
남은 작업 편집 경로와 유지보수 영역을 포함한 전체 UI 수집은 계속 미완료다.
증거: `{D_TEMP}/hpe990/evidence/50c688e3/resume-1791331148631409700/frontier-report.json`,
`resume-1791331176387033200/frontier-report.json`, `inspection/resume-editor-cancel.json`.

버전 0.5를 실제 MCP로 실행하고 Continue를 누른 뒤 Edger로 복귀했다.
세션 `cb812271a87e41f8b41b33ad8f7e4ba6`, HPE990 PID 12676, RAM worker PID 5028이다.
별도 MCP 연결로 실행과 RAM 지속을 재확인했다. 이 값은 검증 당시의 기록이며
현재 상태는 `hpe990_status` 및 `hpe990_ram_status`로 조회한다.

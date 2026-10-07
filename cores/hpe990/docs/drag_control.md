# Native UI ID 드래그

uv 소스 MCP의 `hpe990_ui_drag`로 현재 관찰된 native 요소를 드래그합니다.
Rust worker가 버튼 누름·시간별 이동·해제를 전달하고 RAM이 전후 상태를 기록합니다.

```json
{
  "session_id": "현재 세션 ID",
  "source_ui_id": "수집한 스크롤바 UI ID",
  "start_fraction": [0.5, 0.3],
  "end_fraction": [0.5, 0.55],
  "duration_ms": 500
}
```

- `hpe990_ui_collect`에서 현재 UI ID 확인. 다른 종료 대상은 `target_ui_id`로 지정.
- 시작·종료 좌표는 각 대상 client 영역 내부 비율이며 두 값 모두 0보다 크고 1보다 작아야 함.
- 이동 시간은 50~5000ms. 모호한 ID, 숨김·비활성 조상, 가시 영역 밖 지점 및 바뀐 geometry 거부.
- 정상 종료는 Rust가 버튼을 한 번 해제. 타임아웃/worker 해제 실패는 Python이 보완 해제.
- 전달 방식은 현재 process-scoped Win32 messages. OS 전체 마우스 이동/물리 입력 API가 아님.
- 반환값의 `worker.ok`는 전달 결과. `application_result_verified: false`이므로
  `before`/`after` 증거를 기대 동작과 비교해야 실제 앱 성공 판정 가능.
- 실제 BDD는 General 스크롤바 이동·원위치 복원을 3회 검증. 다른 요소 간
  drag-and-drop 의미 동작과 OCR 전용 요소 제어는 아직 실제 검증되지 않음.
- 배포 EXE는 갱신하지 않음. Rust worker는 외부 `D_TEMP/hpe990/build/input/` 사용.

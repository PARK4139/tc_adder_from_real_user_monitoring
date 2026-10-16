# Real Activity Monitoring timestamp 병렬 로그

Real Activity Monitoring 시작 시 독립 writer가 자동 연결되어 native/semantic `events.jsonl`을 읽고,
`{D_TEMP}/hpe990/runtime/activity-log/{session_id}/activity.log`에 지속 기록합니다.
별도 MCP 도구는 없습니다. 기존 `hpe990_ram_start`의 `activity_log` 결과와
`hpe990_ram_status`에서 경로·writer 상태·오류를 확인합니다.

형식은 `시간대 포함 ISO 8601 INFO {JSON 상세}`입니다. JSON에는 stream, session_id,
run_id, sequence, ui_id(미식별 시 unidentified), 변화 종류, 원본 관측 시각·epoch ms,
로그 기록 시각·epoch ms, 원본 파일·offset 및 원본 이벤트 전체가 들어갑니다.
전후 내용, 이미지와 스냅샷 참조는 원본 event에 보존합니다. 원본 JSONL은 수정하지 않습니다.

- 관측 시각은 실제 발생 시각이 아닙니다. OCR·색상 등의 의미를 추정하여 확정하지 않습니다.
- `available_unix_ms`는 writer가 완성된 원본 행을 처음 읽을 수 있었던 시각입니다.
  p99는 그 시각부터 durable append 완료까지 측정합니다. 이전 이벤트의 backfill과
  원본 관측 지연은 이 수치와 구분합니다. polling 간격은 100ms입니다.
- 부분 원본 행은 다음 poll에서 재시도합니다. 쓰기 실패 시 읽기 위치를 진행하지 않고
  `status.json`에 오류를 남깁니다. 종료 시 남은 완성 행을 기록하고 flush합니다.
- native/semantic 순번은 합치지 않습니다. 재시작 시 로그의 stream/run_id/sequence로
  중복을 방지하고 마지막 불완전 로그 행만 복구합니다.
- 모든 연결된 수집기가 종료되면 writer도 종료합니다. writer 실패는 Emulator나 RAM을
  종료하지 않습니다. 다음 Real Activity Monitoring 시작 호출은 종료된 writer를 다시 연결합니다.
- 시작·종료, observation_gap 및 늦은 이벤트도 원본 종류와 시각을 그대로 보존합니다.
  전체 UI 및 모든 순간 변화가 감지됐다는 의미는 아닙니다.

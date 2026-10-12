# RAM registry isolation and observation freshness

## Registry access

Canonical UI identities and semantic mappings use SQLite WAL through
`functions/identity_database.py`. Connections close explicitly after transactions.
Readers can retain a consistent snapshot while another connection commits identity
observations. A busy writer or journal transition fails within the connection timeout;
WAL does not promise unlimited simultaneous writers or lossless temporal coverage.

The previous DELETE-journal backup retained a read transaction while copying historical
observations. Code inspection, correlated recovery after that reader exited, and an
isolated DELETE-reader/writer reproduction support lock contention as the incident
cause. The original incident has no blocked-thread stack or per-phase timing, so the
entire 241,031.917ms gap cannot be attributed to a single SQLite call.

## Public MCP backup

Call `hpe990_ui_registry_backup(session_id, timeout_seconds=60)` with native RAM active.
The timeout range is 1–300 seconds. The tool preserves a point-in-time snapshot of:

- `elements`: canonical selectors, scopes and allocated numbers.
- `ui_map_targets` and `ui_map_bindings`: version-scoped mappings.
- `sqlite_sequence`: allocator counters, including counters for omitted history tables.

Observation/session-alias history, RAM logs and screenshots remain in their original
storage. This export is **not a full historical backup**. Empty historical tables retain
their schema. The completed database and `manifest.json` are stored under
`D_TEMP/hpe990/evidence/ffba3c51/{session_id}/{backup_id}/`.

The tool checks integrity, foreign keys and counters, includes a SHA-256 digest, and
publishes only a completed file. Timeout/interruption closes readers and removes the
new partial file. An existing destination is never overwritten.

## Observation freshness

`hpe990_ram_semantic_status` and `hpe990_ram_semantic_read` preserve `active` as worker
identity/liveness. `sampling_healthy` reports recent successful observation separately.
`observation_health` contains `state`, `observed_age_ms` and `stale_after_ms`.

States are `stopped`, `starting`, `error`, `stale`, and `observing`. Freshness threshold
is `max(10000, 4 * interval_ms)` milliseconds; an age exceeding it is stale. A new
successful observation automatically restores health. Fresh sampling does not establish
complete window coverage or detection of every transient change.

## Verification

Issues `ffba3c51` and `37b0a63b`: 47 focused tests passed; Ruff passed. WAL isolation
passed three held-reader/writer trials. Real public MCP backup/collection concurrency
passed three trials with native RAM, semantic RAM and activity logging active. Exports
contained 58,144 canonical identities and matched source definitions, counters and maps
exactly; integrity was `ok` with no foreign-key errors. Backup duration was
595.159–1037.891ms; polled observation timestamp gap upper bound was 2440ms and maximum
observed age was 1720ms during this verification window.

A controlled diagnostic pause of only the semantic observer's owning interpreter
verified live-but-stale status at age 12596ms and recovery in the same worker at age
380ms. Native RAM and activity logging stayed active. This intentional diagnostic gap
is recorded separately from the concurrent-backup verification window. The first pause
attempt affected only the Windows virtualenv launcher and did not stop sampling;
its failed assertion/receipts remain preserved.

Receipts and verification JSON: `D_TEMP/hpe990/evidence/{ffba3c51,37b0a63b}/`.
The Emulator was not restarted or driven during these checks. These results do not
close the separate full-UI-inventory issue or imply BDD execution. Changes are validated
in the uv-managed source MCP; the existing one-shot EXE was not rebuilt.

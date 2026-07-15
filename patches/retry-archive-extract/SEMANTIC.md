# retry-archive-extract

## Summary

Adds an HTTP endpoint `POST /sessions/{id}/archives/{id}/retry` and supporting
infrastructure to manually re-trigger Phase 2 (memory extraction) for a
previously failed archive, without re-archiving messages.

## Root Cause

OV archives run Phase 2 extraction as a background async task after commit.
When Phase 2 fails (API overload, timeout, transient error), it writes
`.failed.json` but there is no programmatic way to retry. The archive's
`messages.jsonl` and all infrastructure are intact — only a trigger entry
point is missing.

## Fix

Three changes, all additive (no existing behaviour modified):

1. **`session/session.py` — `_run_memory_extraction`**: Added
   `skip_previous_archive_check: bool = False` keyword-only parameter.
   When `True`, skips `_wait_for_previous_archive_done()` — needed because
   retried archives may have earlier archives with missing `.done`.

2. **`session/session.py` — `retry_archive_extraction(archive_index)`**:
   New method (78 lines). Reads `messages.jsonl` via `_read_archive_messages`,
   deletes `.failed.json` with `os.remove`, creates a task tracker entry,
   and launches `_run_memory_extraction` via `asyncio.create_task` with
   `skip_previous_archive_check=True`. Returns `{task_id, archive_uri,
   message_count}`.

3. **`server/routers/sessions.py` — `retry_archive_session`**:
   New endpoint `POST /sessions/{session_id}/archives/{archive_id}/retry`.
   Delegates to `SessionService.retry_archive()`. Requires trusted-mode
   headers (`X-OpenViking-Account`, `X-OpenViking-User`).

4. **`service/session_service.py` — `retry_archive()`**:
   New method (18 lines). Thin wrapper: loads session, calls
   `session.retry_archive_extraction(int(archive_id))`.

## Verification

- Manually tested against session `11a58a83-c6d4-4294-87bc-b4c0094203f9`
  archive `002` (40 messages, Phase 2 was `cancelled`).
- Phase 2 completed in ~15 seconds, producing 3 add + 3 update operations.
- `.done` written correctly, `.failed.json` deleted via `os.remove`.
- Normal commit path unaffected: `skip_previous_archive_check` defaults to
  `False`, all existing callers omit the kwarg.

## History

- 2026-07-15: Implemented during archive_001 extraction quality review session.
  Prior attempts at independent standalone script failed due to
  `OpenVikingService()` data-directory lock contention with running server.
  HTTP endpoint approach chosen as the zero-downtime solution.

## Prerequisites

This patch assumes `wm-v2-structured-summary-rollback` (commit 5d9ba75) is
already applied, which removes the WM v2 incremental overview-update path
inside `_run_memory_extraction` in favour of per-archive standalone
`structured_summary` generation.

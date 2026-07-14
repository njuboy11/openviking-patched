# WM v2 → structured_summary Rollback

## What
将 `_run_memory_extraction` 中 archive overview 生成从 WM v2 增量更新 (`_generate_archive_summary_async`) 回退为旧版独立摘要 (`_generate_archive_summary`)

## Why
WM v2 增量更新 (`ov_wm_v2_update` + `update_working_memory` tool_call) 在单 session 多 archive 场景下存在结构性缺陷：

- 每个 archive 的 UPDATE 都从同一个 `latest_archive_overview` 出发（非累积式）
- temperature=0.0 + 保守默认偏好 (KEEP > APPEND > UPDATE)
- 导致 7 个 archive 的 overview 逐字节一致

改用 `compression.structured_summary` prompt 独立生成，每个 archive 有独立的内容。

## How
`session.py:1344` 一行改动：`_generate_archive_summary_async` → `_generate_archive_summary`

## Impact
- 仅影响 archive `.overview.md` 生成
- 不影响 long-term memory 提取、embedding、Qdrant 写入
- `_merge_wm_sections` 等 WM v2 函数保留不删（不再被调用）

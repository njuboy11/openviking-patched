# m3-vlm-schema-compat-revert

## Summary
回退 0.4.8 引入的 `delete_uris → delete_ids` JSON Schema 复杂化改动，恢复 0.4.5 时代的简单 `delete_uris: List[str]` 格式，使 MiniMax-M3 能正常输出符合规范的 memory extraction JSON。

## Root Cause
0.4.8 将 `delete_uris: List[str]` 重构为 `delete_ids: List[DeleteId]`（`DeleteId` 是一个带 `delete_page_id` + `replacement_page_id` 的嵌套对象），导致 JSON Schema 复杂度翻倍。M3 无法生成完全符合新 Schema 的 JSON，触发 patch repair retry 或静默返回 0 条记忆。0.4.5 用 M3 完全正常，回归确定在代码侧而非模型侧。

## Fix
三个文件各 3 处改动，核心是 `delete_ids` → `delete_uris`：

### extract_loop.py
- `delete_ids` → `delete_uris`（2 处：import + usage in resolve_operations）
- `_expected_fields = []` → `_expected_fields = ["delete_uris"]`
- `_normalize_delete_ids()` 函数删除，恢复为直接处理 `List[str]`

### schema_model_generator.py
- `delete_ids` → `delete_uris`（3 处：field_definition / is_empty / to_legacy_operations）
- field 类型从 `List[DeleteId]` 回到 `List[str]`
- description 从复杂的 delete_page_id/replacement_page_id 回到简单的 "Delete operations as URI strings"

### 未改动
- `dataclass.py` 中 `DeleteId` 类 + `delete_replacements` 字段保留（内部数据结构不受影响，LLM 只看到 schema 层面）
- `thinking=self.thinking` 参数保留（0.4.5 没有，但 0.4.8 新增，非本次回归根因）

## Verification
- 2026-07-14 18:13-18:20：patch 后触发 session dc2ffc00 archive_009 commit（M3），成功提取 17 条记忆（去重后 13 条），覆盖 events / tools / cases / entities / preferences / trajectories / experiences 共 7 种类型
- 对比 0.4.5 时代（archive_004，0.4.5 + M3）的 memory_diff.json：`content` 字段一致有值

## Affected Files
- `server/openviking/session/memory/extract_loop.py`
- `server/openviking/session/memory/schema_model_generator.py`

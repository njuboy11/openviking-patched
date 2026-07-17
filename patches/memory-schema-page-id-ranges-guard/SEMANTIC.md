# Memory schema: page_id 只对非 ranges 类型暴露

## 影响文件
`openviking/session/memory/schema_model_generator.py` — `SchemaModelGenerator` 类（约 117 行附近）

## 问题

`SchemaModelGenerator` 在拼装每个 memory 类型（preferences / projects / events / trajectories / …）的 Pydantic 字段定义时，**无条件**塞进一个 `page_id: int` 字段（`Field(..., description="Temporary page_id for identifying the target memory item.")`）。

LLM 收到这个 schema 后，对 **所有** memory 类型都会尝试填 `page_id`。但下游 `apply_operations` 里的 URI 解析流程是两条分支：

| 路径 | 触发条件 | URI 来源 |
|------|---------|----------|
| page_id → URI | LLM 填了 page_id | `page_id_map.resolve(page_id)` |
| ranges → URI | LLM 填了 message ranges | `_range_targets(ranges)` 计算 |

对于 events / trajectories 这种**纯 ranges 路由**的 memory 类型，`page_id_map` 里根本没条目，`page_id_map.resolve(...)` 直接返回空 → `apply_operations` 抛 `ValueError: Cannot apply operations: missing resolved URIs for events(page_id=105)` → 整个 commit batch 崩溃 → archive Phase 2 失败。

历史上这个错在 8 个 archive 上都出现过：page_id 100/101/102/103/104/105/111/112，全是 events / trajectories 类型。

## 修改

只在 `has_ranges=False` 的 schema 上注册 `page_id` 字段，ranges 类型走纯 ranges 路由：

```python
# 原（无条件加 page_id）：
field_definitions["page_id"] = (
    Annotated[int, WithJsonSchema({"type": "integer"})],
    Field(
        ...,
        description="Temporary page_id for identifying the target memory item.",
    ),
)

# 改（只在非 ranges schema 加）：
# page_id is only meaningful for file-backed schemas (e.g. preferences, projects).
# For message-range schemas (e.g. events, trajectories) the LLM should use the
# "ranges" field instead, because the page_id map only holds file URIs.
if not has_ranges:
    field_definitions["page_id"] = (
        Annotated[int, WithJsonSchema({"type": "integer"})],
        Field(
            ...,
            description="Temporary page_id for identifying the target memory item.",
        ),
    )
```

## 为什么只 guard `if not has_ranges`

- `has_ranges` 是 schema 里早就存在的判别字段（events / trajectories = True，其余 = False），不需要新增字段
- 已有 Pydantic schema 的 memory 类型全部走 `has_ranges` 二选一分支，guard 写在这里就堵死所有上游 schema 误填
- 配合 patch `apply-ops-skip-unresolved-uri`，即使 LLM 偶尔漏判 / 乱填，`apply_operations` 也会跳过而不是崩

## 在 0.4.9 上的状态

0.4.9 没有这个 guard。**未升级前 events / trajectories 类型的 archive 仍然会失败**，需配合 patch `apply-ops-skip-unresolved-uri`（不崩但跳过）一起使用。

## 升级时如何重打

1. 备份 0.4.9 官方 `schema_model_generator.py`
2. 找到 `field_definitions["page_id"] = (` 那段（紧跟某个 `if has_ranges:` / `if not has_ranges:` 分支之后）
3. 把整段 `field_definitions["page_id"] = ...` 嵌套到 `if not has_ranges:` 里
4. 不要用机械 patch 工具 — 必须手动 wrap，避免把后面的 `for field in memory_type.fields:` 循环吞掉
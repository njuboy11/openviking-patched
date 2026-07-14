# OpenViking Patched

自维护的 OpenViking 分叉。基于上游 v0.4.9 + 6 个本地补丁（上次更新：2026-07-14）。

## 仓库结构

```
server/openviking/   → 完整服务端代码（v0.4.9 + 全部补丁已打入）
plugin/openviking-plugin/ → OpenClaw 插件代码（与官方 npm 2026.7.11 完全一致）
patches/             → 独立 .patch 文件，每个修复一个
```

## 当前生效补丁（6 个，全部在 0.4.9 仍需）

| patch | 文件 | 修复内容 | 上游 |
|-------|------|----------|------|
| `PR2619-rerank-non-empty-docs.patch` | `models/rerank/openai_rerank.py` | Rerank 过滤空文档，防止 SiliconFlow 400 | PR #2619 open |
| `PR2619-batch-read-concurrent.patch` | `storage/viking_fs.py` | read_batch 并发 asyncio.gather | PR #2619 open |
| `PR3135-l2-document-recall.patch` | `retrieve/hierarchical_retriever.py` | 恢复 L2 文档级召回 | PR #3135 merged |
| `PR3172-root-context-and-abstract.patch` | `session/session.py` | ROOT context + abstract 跳过标题 | PR #3172+#3137 |
| `reindex-vectors-l2-only.patch` | `service/reindex_executor.py` | vectors_l2_only 重索引 | 本地 |
| `memory-updater-vlm-summary.patch` | `session/memory/memory_updater.py` | VLM summary 优先 | 本地 |

## 版本基线

| 组件 | 版本 |
|------|------|
| OV 服务端 | **v0.4.9** + 6 patched files |
| OV 插件 | 2026.7.11 |
| OpenClaw | 2026.7.1 |

## 升级记录

- `pre-0.4.9-baseline` — v0.4.8 + 6 patches 锚点 tag
- 2026-07-14 — 升级 0.4.9，6 个 patch 全部重打（0.4.9 均未合入）

## 同步规则

- 本地 OV 服务端 = 仓库 server/ 目录
- 本地 OV 插件 = 仓库 plugin/ 目录
- patches/ 只保留实际在用的补丁

# OpenViking Patched

自维护的 OpenViking 分叉。基于上游 v0.4.8 + 6 个本地补丁。

## 仓库结构

```
server/openviking/   → 完整服务端代码（v0.4.8 + 全部补丁已打入）
plugin/openviking-plugin/ → OpenClaw 插件代码（与官方 npm 2026.7.11 完全一致）
patches/             → 独立 .patch 文件，每个修复一个
```

## 当前生效补丁（6 个）

| patch | 文件 | 修复内容 | 上游状态 |
|-------|------|----------|----------|
| `PR2619-rerank-non-empty-docs.patch` | `models/rerank/openai_rerank.py` | Rerank 过滤空文档，防止 SiliconFlow 400 | PR #2619 open |
| `PR2619-batch-read-concurrent.patch` | `storage/viking_fs.py` | read_batch 并发 asyncio.gather 替代串行 | PR #2619 open |
| `PR3135-l2-document-recall.patch` | `retrieve/hierarchical_retriever.py` | 恢复 L2 文档级召回命中（0.4.7 回归） | PR #3135 merged |
| `PR3172-root-context-and-abstract.patch` | `session/session.py` | ROOT context 绕过 peer 隔离 + abstract 跳过 markdown 标题 | PR #3172 + #3137 |
| `reindex-vectors-l2-only.patch` | `service/reindex_executor.py` | vectors_l2_only 重索引模式，跳过 L0/L1 直接到 SKILL.md | 本地 patch |
| `memory-updater-vlm-summary.patch` | `session/memory/memory_updater.py` | VLM summary 优先于全文 fallback | 本地 patch |

## 版本基线

| 组件 | 版本 | 来源 |
|------|------|------|
| OV 服务端 | v0.4.8 + 6 patched files | pip install openviking==0.4.8 |
| OV 插件 | 2026.7.11 | npm @openviking/openclaw-plugin |
| OpenClaw | 7.1-beta.6 | npm openclaw |

## 升级检查清单

升级到新版本后需逐个核查这 6 个 patch 是否仍需重新打入：

- [ ] `models/rerank/openai_rerank.py` — PR #2619
- [ ] `storage/viking_fs.py` — PR #2619
- [ ] `retrieve/hierarchical_retriever.py` — PR #3135
- [ ] `session/session.py` — PR #3172 + #3137
- [ ] `service/reindex_executor.py` — vectors_l2_only
- [ ] `session/memory/memory_updater.py` — VLM summary

## 同步规则

- 本地 OV 服务端 = 仓库 server/ 目录（单向同步：本地 → 仓库）
- 本地 OV 插件 = 仓库 plugin/ 目录（单向同步：本地 → 仓库）
- patches/ 目录只保留实际在用且未合入上游的补丁

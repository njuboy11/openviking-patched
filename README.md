# OpenViking Patched

自维护的 OpenViking 分叉。基于上游 v0.4.9 + 6 个本地补丁，语义文档驱动升级。

## 仓库结构

```
server/openviking/   → 完整服务端代码（v0.4.9 + 补丁已打入）
plugin/openviking-plugin/ → OpenClaw 插件代码
patches/             → 6 个语义文档，每个补丁一个目录
```

## 补丁目录（6 个）

| 目录 | 文件 | 说明 | 0.4.9 冲突 |
|------|------|------|------------|
| `PR2619-rerank-non-empty-docs/` | openai_rerank.py | Rerank 空文档过滤 | 无冲突 |
| `PR2619-batch-read-concurrent/` | viking_fs.py | read_batch 并发优化 | ⚠️ 手动改（0.4.9 加了 image_url） |
| `PR3135-l2-document-recall/` | hierarchical_retriever.py | L2 文档级召回 | 无冲突 |
| `PR3172-root-context-and-abstract/` | session.py | ROOT context + abstract 修正 | ✅ 0.4.9 无改动 |
| `reindex-vectors-l2-only/` | reindex_executor.py | vectors_l2_only 重索引 | ✅ 0.4.9 无改动 |
| `memory-updater-vlm-summary/` | memory_updater.py | VLM summary 优先 | ✅ 0.4.9 无改动 |

## 升级流程

1. pip install 新版本
2. 3 个 0.4.9 无改动的文件直接 copy 备份恢复
3. 3 个 0.4.9 有改动的文件，打开对应的 SEMANTIC.md，按说明手动改
4. 重启 OV → 验证 recall / search / auto-recall

## 版本历史

- `pre-0.4.9-baseline` — v0.4.8 + 6 机械 diff patch 锚点
- 2026-07-14 — 升级 0.4.9，发现机械 patch 不适配，改为语义文档驱动

# OpenViking Patched

自维护的 OpenViking 分叉。基于上游 v0.4.8 + 本地补丁，不再跟主仓库走。

## 仓库结构

```
server/openviking/   → 完整服务端代码（v0.4.8 + 补丁已打入）
plugin/openviking-plugin/ → OpenClaw 插件代码
patches/             → 独立 .patch 文件
```

## 当前生效补丁

| patch | 文件 | 修复内容 |
|-------|------|----------|
| `models-rerank-openai_rerank.py.patch` | `models/rerank/openai_rerank.py` | PR #2619 — Rerank 过滤空文档，防止 OpenAI API 400 |

## 服务端基线

| 版本 | 说明 |
|------|------|
| v0.4.8 | pip 安装基线（已包含 PR #3135 / #3137 / #3143 / #3172 等上游合入项） |
| PR #2619 | 本地 patch，上游仍未合入，需持续维护 |

## 插件基线

| 版本 | 说明 |
|------|------|
| 2026.7.11 | OpenClaw bundled 插件，与本地 `/root/.openclaw/extensions/openviking/` 完全一致 |

## 历史废弃补丁（已回滚删除）

以下补丁曾应用于 v0.4.5 时期，升级到 v0.4.8 后已由上游原生支持，不再需要：

- 10 个 memory template yaml 补丁（`prompts/templates/memory/*.yaml`）
- `schema_model_generator-summary-required.patch`
- `session-memory-memory_updater.py.patch`
- `plugin-context-lifecycle-fallback-token-budget.patch`

## 同步规则

- 本地 OV 服务端 = 仓库 server/ 目录（单向同步：本地 → 仓库）
- 本地 OV 插件 = 仓库 plugin/ 目录（单向同步：本地 → 仓库）
- patches/ 目录只保留本地实际在用的补丁

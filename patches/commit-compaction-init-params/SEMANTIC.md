# commit-compaction-init-params

## Summary
调整 OV Plugin fallback 路径的硬上限，从 200_000 tokens 提升到 300_000 tokens。

## Root Cause
0.4.10 Plugin 已包含 `safeFallbackTruncate` 函数（L389），但 `MAX_FALLBACK_TOKENS = 200_000`（L172）的硬上限太保守 — 在长对话 + 自动注入 recall 上下文的场景下，20 万 tokens 不足以覆盖单次 commit 后 compact 阶段的完整消息体，导致 `assemblePassthrough` 在 12 条 fallback 路径里反复触发截断（消息被从头部逐条丢弃到 ≤ 20 万 tokens），重要上下文被截掉。

## Fix
**单行修改** `plugin/openviking-plugin/services/context-lifecycle-service.ts`：

```diff
- const MAX_FALLBACK_TOKENS = 200_000;
+ const MAX_FALLBACK_TOKENS = 300_000;
```

`safeFallbackTruncate` 函数（L389-L407）的语义不变：
```ts
const cap = Math.min(tokenBudget, MAX_FALLBACK_TOKENS);
// 从头部逐条丢弃直到 roughEstimate(truncated) <= cap
```

## Affected Versions
- **0.4.10 Plugin (2026.7.15)**：默认 200_000，需要本 patch 升到 300_000
- 0.4.9 及更早版本：plugin 没有 fallback truncate，需要先打原始 plugin-fallback-safe-truncate patch

## Changed File
`plugin/openviking-plugin/services/context-lifecycle-service.ts`（L172）

## Why 30 万不是 100 万
鹏哥拍板：`maxActiveTranscriptBytes` 是 1MB（约 25-30 万 tokens）。把硬上限设到 30 万等于"刚好不溢出"。再大就回到"原始 1MB 全量 messages"问题。

## Verification
- live plugin 已应用本 patch（`/root/.openclaw/extensions/openviking/services/context-lifecycle-service.ts` L172 = 300_000）
- fallback 路径触发时日志显示 `truncated N→M messages, X→Y tokens (cap=300000, budget=...)`
- 不再因 fallback 截断导致关键上下文丢失
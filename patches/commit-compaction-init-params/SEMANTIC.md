# plugin-fallback-safe-truncate

## Summary
修复 OV Plugin fallback 路径在全量消息送给大模型导致上下文溢出（1MB+ raw messages）的问题。

## Root Cause
`assemblePassthrough` 函数在 12 条 fallback 路径（OV server 超时/500/session_not_found/auto_recall_disabled 等）被调用时，原封不动返回全量 `liveMessages`，不做任何 token budget 截断。当累积消息接近 `maxActiveTranscriptBytes: 1MB` 时，大模型直接报上下文溢出。

## Fix
- 新增 `MAX_FALLBACK_TOKENS = 200_000` 硬上限
- 新增 `safeFallbackTruncate` 函数：按 `min(tokenBudget, MAX_FALLBACK_TOKENS)` 做消息截断（从头部逐条丢弃）
- 修改 `assemblePassthrough` 签名：接收 `roughEstimate`/`tokenBudget`/`logger` → 调用 `safeFallbackTruncate` 后再返回
- 更新所有 12 个 `assemblePassthrough` 调用点 + catch 块最后一条 fallback，全部传入截断所需参数
- 总计改动 ~50 lines

## Affected Versions
- OV Plugin bundled with OpenClaw v2026.7.1（本次修复针对此版本）
- 0.4.8 及更早版本的 plugin 也存在此问题

## Changed File
`plugin/openviking-plugin/services/context-lifecycle-service.ts`

## Verification
修复后，fallback 时刻消息被截断至 ≤200k tokens，不再溢出。

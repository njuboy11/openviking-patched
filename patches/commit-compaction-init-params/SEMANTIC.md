# commit-compaction-init-params

## Summary
OV Plugin fallback 路径的硬上限从 30万 tokens 调回 20万 tokens（patch #7 升 30万 → 本次 reverse 回 20万）。

## Root Cause
patch #7 把硬上限从 200_000 升到 300_000 是为了避免 `safeFallbackTruncate` 反复截断长对话。

但实测发现 **30 万 token 单次 compact 跑不完**：

- 2026-07-18 16:57:23 OV 触发 compact（tokenBudget=300000），卡在 archive extract 阶段
- 17:00:32 gateway 被 systemd 强杀 → compact 未完成 → 工作进度未 commit → 新 session 看不到
- 单次 compact 太重 = 重启强杀时丢上下文风险高

## Fix
**单行修改** `plugin/openviking-plugin/services/context-lifecycle-service.ts`：

```diff
- const MAX_FALLBACK_TOKENS = 300_000;
+ const MAX_FALLBACK_TOKENS = 200_000;
```

回退到 0.4.10 plugin 默认值。

## Why 改回 20万
鹏哥 2026-07-18 17:11 拍板：

- **更频繁的 commit** = 单次 compact token 量更小 = 重启时更可能已 commit
- **重启丢上下文根因**：300k compact 没跑完被强杀 → 工作进度未持久化
- 接受 patch #7 提到的"长对话 fallback 截断"风险（20万硬上限 → 部分超长消息会被截），但**更看重"重启时进度不丢"**

## Trade-off
- 接受：长对话（接近 20万 tokens）触发 fallback 截断风险（patch #7 的原根因）
- 缓解：
  - systemd `KillSignal=SIGTERM + TimeoutStopSec=30` 给 OV flush 窗口
  - 用 patch #17 retry-archive-extract 在 stuck 时手动重跑

## Changed File
`plugin/openviking-plugin/services/context-lifecycle-service.ts`（L172）

## Verification
- live plugin 已应用：`.ts L172 = 200_000`，`.js dist L20 = 200_000`
- sha256 已校验
- 备份：`.bak-1784366025-pre-fallback-cap-200k`

## Related
- patch #7 (commit 04af535)：原 20万→30万 升
- patch #17 (retry-archive-extract)：stuck compact 时手动 retry 兜底

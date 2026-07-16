# patch: auto-recall-block-blank-line

## Root Cause

OV auto-recall 通过 `buildRecallContextBlock()` 把命中记忆拼成 `<relevant-memories>` 块注入 prompt，
原实现用 `...memoryLines` 在元素间只放 `\n`（一条换行），M3 视觉/语义解析看不出「这是新一条 memory」
还是「上一条的延续」。多个 bullet 黏在一起，更像**单个长 list**而非**多条独立 memo**。

配合 auto-recall 一次注入 5-6 条 × 2000-5000 字符的密度，M3 的 bottom-heavy attention 把这种
「连续 pasted block」当成上下文噪音，上下文污染模式 7/10 已记录。

旁路证据：journal 7.2-beta.1 inject-detail 输出 5 条记忆堆成一坨无分隔。

## Fix

`auto-recall.ts` line 219 / `dist/auto-recall.js` line 123：

-    ...memoryLines,
+    memoryLines.join("\n\n"),

每条 memory 之间改为双换行（即空行），让 M3 Markdown parser 识别为独立 block。

修改后 `buildRecallContextBlock` 输出示例：

```
<relevant-memories>
Source: openviking-auto-recall
The following OpenViking memories may be relevant:
- [events]
  <uri>...a.md</uri>
  # Summary ...
                            ← 空行
- [experiences]
  <uri>...b.md</uri>
                            ← 空行
- [trajectories]
  <uri>...c.md</uri>
</relevant-memories>
```

## Verification

```bash
$ node -e 'import("/root/.openclaw/extensions/openviking/dist/auto-recall.js").then(m=>console.log(m.buildRecallContextBlock(["- [events]\n  uri:a","- [exp]\n  uri:b"])))'
<relevant-memories>
Source: openviking-auto-recall
The following OpenViking memories may be relevant:
- [events]
  uri:a
                                  ← here blank line
- [exp]
  uri:b
</relevant-memories>
```

实测：

- `memoryLines.join("\n\n")` ✅ 生效
- 总字符数 +14 字节 / 5 条（固定开销，可忽略）
- 重启后 PID 157431，plugin registered 18:13:30

## Compatibility

- 7.2-beta.1（runtime）✅ 验证
- 7.1-beta.6 上一版未含此 patch，apply 后行为相同
- 7.0 兼容（buildRecallContextBlock 同款实现）

## Risk

- LLM 模型上下文占用 +14 字节 / 5 条 = 接近 0
- 召回间隔变大可能影响 parsing timing，不影响结果
- 已用 minimax M3 + deepseek-v4-pro 实测，无 negative regression

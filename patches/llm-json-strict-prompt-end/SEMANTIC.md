# llm-json-strict-prompt-end

## Summary
在 `get_json_schema_prompt` 生成的 JSON schema instruction 末尾追加中文严格输出指令，去掉原末尾冗余的 "Only output JSON, no other text"，修复 MiniMax-M3 在 OV memory extraction 和 WM v2 update 场景下的间歇性 ParseError。

## Root Cause
- MiniMax-M3 不支持 OpenAI `response_format: {type: "json_object"}` 参数（鹏哥 7/15 11:36 官方确认）
- OV 的 `StructuredVLM.complete_json` / `complete_json_async` 通过 `get_json_schema_prompt` 把 JSON schema 注入到 prompt 文本里（`models/vlm/llm.py:121`）
- 原 prompt 末尾只有 "Only output JSON, no other text" 一句弱约束，M3 在 tool_call 增量更新（WM v2 UPDATE）和 ReAct memory extraction 场景下容易：
  - 输出 JSON 前后夹带解释文字 / markdown fence
  - 输出截断
  - 字段命名错误
- 这些情况 json_repair（`llm.py:75` + `memory/utils/json_parser.py:73`）部分能修，但间歇性 ParseError 仍触发
- 鹏哥提供的中文严格指令文本（7/15 11:36）作为 prompt 末尾强约束，比原英文末尾约束强度更高

## Fix
`models/vlm/llm.py:129-145 get_json_schema_prompt` 一处改动：

### 修改前（v0.4.9 原始）
```python
prompt = f"""Please output the result in JSON format.

Output format requirements:
```json
{schema_str}
```
"""
if description:
    prompt += f"\n{description}\n"

prompt += "\nOnly output JSON, no other text."
return prompt
```

### 修改后（本版本）
```python
prompt = f"""Please output the result in JSON format.

Output format requirements:
```json
{schema_str}
```

你只能输出标准JSON，禁止任何解释文字、前言、markdown、换行注释，直接返回可JSON.parse的纯JSON字符串。
"""
if description:
    prompt += f"\n{description}\n"

return prompt
```

### 关键变化
- 末尾追加中文强约束（鹏哥原文）
- 删除原末尾 "Only output JSON, no other text"（被强约束覆盖）
- 开头 "Please output the result in JSON format" 保持不变（鹏哥决策 7/15 11:51）

## Verification
- 2026-07-15 11:46：commit `5e8b001` push 到 `openviking-patched` 仓库
- 2026-07-15 11:46：OV server `systemctl restart openviking-server`，health endpoint 返回 `{"status":"ok","healthy":true,"version":"0.4.9","auth_mode":"trusted"}`
- 后续验证（鹏哥主动触发新 commit 时）：看 `.failed.json` 是否仍出现 + memory_diff.json 格式是否合法

## Affected Files
- `server/openviking/models/vlm/llm.py`（OV 端代码，重启生效）
- OpenClaw plugin 端无改动
- Qdrant 数据无迁移

## History
- v1 (commit 4b9d65f, 7/15 11:46, 已废弃 via force push): 强约束放在 prompt 开头
- v2 (commit 5e8b001, 7/15 11:54, 最终): 强约束放在 prompt 末尾

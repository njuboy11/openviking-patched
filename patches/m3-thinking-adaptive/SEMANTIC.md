# M3 Thinking Adaptive — MiniMax-M3 VLM `thinking.type=adaptive` 配置指南

## 问题

MiniMax-M3 在作为 OpenViking VLM 提取记忆时，非 thinking 模式下提取质量差于 thinking 模式：

| 维度 | 无 thinking (archive_009) | thinking=adaptive (archive_013) |
|---|---|---|
| 结构一致性 | trajectories 字段常空缺 | 5 条全部填满 Domain/Trigger/Preconditions/Procedure/Anti-patterns |
| 反模式捕获 | 偶有遗漏 | 每条 trajectory 都有 Anti-patterns 块 |
| SOP 深度 | experiences 3-4 步 | 12 步 + 9 项 Reflect |
| tool 更新质量 | 泛泛描述 | 带真实 URL + 根因分析（GitHub tag 格式 v6.11.0 vs v2026.6.11） |

## 根因

MiniMax M3 的 `thinking` 参数通过 OpenAI Python SDK 的 `extra_body` 机制注入为请求 JSON 的顶级字段。OpenViking 0.4.9 已内置 `extra_request_body` → `extra_body` 转发链路，无需修改代码。

## 配置

在 `ov.conf` 的 `vlm` 段添加：

```json
"vlm": {
  "provider": "openai",
  "api_base": "https://api.minimaxi.com/v1",
  "api_key": "sk-...",
  "model": "MiniMax-M3",
  "max_tokens": 32768,
  "timeout": 600,
  "max_concurrent": 2,
  "extra_request_body": {
    "thinking": {
      "type": "adaptive"
    }
  }
}
```

## 生效原理

```
ov.conf extra_request_body
  → base.py:73  self.extra_request_body = dict(config.get("extra_request_body") or {})
  → openai_vlm.py:144  _apply_provider_specific_extra_body() merges into kwargs["extra_body"]
  → openai_vlm.py:306  client.chat.completions.create(**kwargs)
  → OpenAI SDK merges extra_body keys into request JSON root
  → POST /v1/chat/completions body 包含 "thinking": {"type": "adaptive"}
```

## 兼容性

- **MiniMax M3 API** 直接接受 `{"thinking": {"type": "adaptive"}}` 作为顶级 JSON 字段，无需特殊 wrapper
- **其他 OpenAI 兼容 provider**（DeepSeek V4、Qwen 等）若 API 不接受额外字段，OpenAI SDK 的 `extra_body` 由各 provider 自行忽略，不影响正常请求
- **不需要改任何 Python 代码** — 0.4.9 的 `extra_request_body` 转发是通用机制

## 与 m3-vlm-schema-compat-revert 的配合

`m3-thinking-adaptive` 和 `m3-vlm-schema-compat-revert` 是两个独立 patch，共同生效：

- `schema-compat-revert` 解决 **格式兼容性**：回退 0.4.8 引入的 `delete_uris→delete_ids` 嵌套结构，让 M3 能正确输出 JSON
- `thinking-adaptive` 解决 **提取质量**：在格式兼容基础上启用 thinking 模式，提升结构一致性和深度

两者必须同时应用才能获得稳定 + 高质量的记忆提取。

## 验证方法

1. 修改 ov.conf VLM 段加入 `extra_request_body`
2. 重启 OV server
3. 等待一次 archive extraction 完成
4. 检查 `memory_diff.json` 中 trajectory 类记忆的字段完整性（Domain/Trigger/Preconditions/Procedure/Anti-patterns 是否全部填充）
5. 对比 `extract_loop.py` telemetry 中 rerank tokens 和质量指标

## 版本

- 适用版本：OpenViking 0.4.9+
- 配置方式：纯 ov.conf 配置，0 行代码改动
- 依赖：MiniMax-M3 API（需支持 thinking 参数）

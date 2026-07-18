# M3 Thinking Adaptive — MiniMax-M3 VLM `thinking.type=adaptive` 配置指南

## 状态

- **0.4.10 verified**（2026-07-18）：live OV 0.4.10 已原生支持 `extra_request_body` → `extra_body` 转发链路，零代码改动
- **0.4.9+ 适用**：内建 `extra_request_body` 字段
- **配置方式**：纯 `ov.conf` JSON 配置，无 Python 改动

## 问题

MiniMax-M3 在作为 OpenViking VLM 提取记忆时，非 thinking 模式下提取质量差于 thinking 模式：

| 维度 | 无 thinking (archive_009) | thinking=adaptive (archive_013) |
|---|---|---|
| 结构一致性 | trajectories 字段常空缺 | 5 条全部填满 Domain/Trigger/Preconditions/Procedure/Anti-patterns |
| 反模式捕获 | 偶有遗漏 | 每条 trajectory 都有 Anti-patterns 块 |
| SOP 深度 | experiences 3-4 步 | 12 步 + 9 项 Reflect |
| tool 更新质量 | 泛泛描述 | 带真实 URL + 根因分析（GitHub tag 格式 v6.11.0 vs v2026.6.11） |

## 根因

MiniMax M3 的 `thinking` 参数通过 OpenAI Python SDK 的 `extra_body` 机制注入为请求 JSON 的顶级字段。OpenViking 0.4.9+ 已内置 `extra_request_body` → `extra_body` 转发链路，无需修改代码。

## 配置（鹏哥已应用，2026-07-18 16:40）

`/root/.openviking/ov.conf` `vlm` 段：

```json
"vlm": {
  "provider": "openai",
  "api_base": "https://api.minimaxi.com/v1",
  "api_key": "sk-...",
  "model": "MiniMax-M3",
  "max_tokens": 262144,
  "timeout": 600,
  "max_concurrent": 2,
  "extra_request_body": {
    "thinking": {
      "type": "adaptive"
    }
  }
}
```

## 生效原理（live 0.4.10 verified）

```
ov.conf extra_request_body                          [配置层]
  → base.py:73  self.extra_request_body = dict(config.get("extra_request_body") or {})  [实例化]
  → openai_vlm.py:144 _apply_provider_specific_extra_body() 合并进 kwargs["extra_body"]  [转换]
  → openai_vlm.py:306 client.chat.completions.create(**kwargs)                          [SDK 调用]
  → OpenAI SDK 把 extra_body 字段 merge 到请求 JSON 根级                              [网络]
  → POST api.minimaxi.com/v1/chat/completions body 含 "thinking": {"type": "adaptive"} [打到 M3]
```

关键代码位置（live 0.4.10 验证）：
- `/usr/local/lib/python3.12/dist-packages/openviking/models/vlm/base.py:73` 读 extra_request_body
- `/usr/local/lib/python3.12/dist-packages/openviking/models/vlm/backends/openai_vlm.py:144-152` 应用 _apply_provider_specific_extra_body
- `/usr/local/lib/python3.12/dist-packages/openviking/models/vlm/backends/openai_vlm.py:215-243` _build_text_kwargs 调用 _apply

## 兼容性

- **MiniMax M3 API** 直接接受 `{"thinking": {"type": "adaptive"}}` 作为顶级 JSON 字段
- **`_supports_enable_thinking()` 默认 False for non-DashScope host**：minimaxi.com host 不在 `_DASHSCOPE_HOSTS`，所以 `enable_thinking` 不会自动注入——只有我们写的 `extra_body.thinking.type=adaptive` 原样透传 ✓
- **0 行代码改动**：仅 ov.conf JSON 配置，不需要 rebuild OV / pip reinstall

## 与 m3-vlm-schema-compat-revert 的配合

两个独立 patch，共同生效：

- **`schema-compat-revert`**：回退 0.4.8 引入的 `delete_uris→delete_ids` 嵌套结构 → 让 M3 能正确输出 JSON 格式
- **`thinking-adaptive`**（本 patch）：启用 thinking 模式 → 让 M3 输出格式+内容都好

两者必须同时应用才能获得稳定 + 高质量的记忆提取。

## 验证方法

1. ✓ `ov.conf` 已加 `extra_request_body.thinking.type=adaptive`
2. ✓ OV 0.4.10 原生支持，已转发
3. 等待一次 archive extraction 完成
4. 检查 `memory_diff.json` 中 trajectory 类记忆的字段完整性（Domain/Trigger/Preconditions/Procedure/Anti-patterns 是否全部填充）
5. 对比 `extract_loop.py` telemetry 中 rerank tokens 和质量指标

## 历史 commit

2026-07-18 16:40 鹏哥拍板：patch #10 m3-thinking-adaptive 应用，确认 0.4.10 native + ov.conf 已配 = 0 改动生效。

# PR3172 + PR3137 — ROOT context + abstract 修正

## 影响文件
`openviking/session/session.py`

## 修改 A：ROOT context（PR3172）

在 `_run_long_term_memory_extraction()` 和 `extract_execution_memories()` 两个方法里，用 `Role.ROOT` 代替 session 自带 `self.ctx`（可能为 USER role）。

**原因**：auth middleware 在 trusted 模式下给 ctx 赋 USER role，触发 peer-isolation 检查，阻止 extract 写入 `peers/<id>/memories/` 路径。Extract 是 session 的**内部操作**，需要完整读写权限。

只需要在调用前临时构建一个新 ctx：
```python
extract_ctx = RequestContext(user=self.ctx.user, role=Role.ROOT, actor_peer_id=self.ctx.actor_peer_id)
```

## 修改 B：abstract 跳过 markdown 标题（PR3137）

`_extract_summary_line()` 方法：原逻辑用 regex 匹配 `**Title**: content` 格式提取，0.4.7 后 LLM 输出的 summary 格式变多（含 `#`, `---` 等），导致 abstract 返回空或错误内容。

改为逐行扫描，跳过空行 / `#` 标题 / `---` 分隔线，取第一段可用文本（>3 字符）。

## 在 0.4.9 上的状态

session.py 在 0.4.9 零改动，两处修改直接 copy 即可。

## 升级时如何重打

两处修改互不冲突，直接用备份文件覆盖，或手动在对应方法位置修改。

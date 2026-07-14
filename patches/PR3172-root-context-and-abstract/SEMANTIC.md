# PR3172 + PR3137 — ROOT context + abstract 修正

## 影响文件
`openviking/session/session.py`

## 修改 A：ROOT context（PR3172）

### 问题
Auth middleware 在 trusted 模式下给 session 的 `self.ctx` 赋 USER role，触发 peer-isolation 检查，阻止 extract 写入 `peers/<id>/memories/` 路径。但 extract 是 session 的**内部操作**，需要完整读写权限才能正常提取记忆。

### 改动

在 `_run_long_term_memory_extraction()` 和 `extract_execution_memories()` 两个方法中，构建专用 ROOT context 代替 session 自带 `self.ctx`：

```python
# 在 _run_long_term_memory_extraction 调用之前插入
extract_ctx = RequestContext(
    user=self.ctx.user,
    role=Role.ROOT,
    actor_peer_id=self.ctx.actor_peer_id,
)
# 然后所有内部调用用 extract_ctx 代替 self.ctx
```

找到的锚点：`if long_term_has_work:` 这个条件块内部，session_compressor 的所有调用（约 3 处 `ctx=self.ctx`），改为 `ctx=extract_ctx`。

## 修改 B：abstract 跳过 markdown 标题（PR3137）

### 问题
`_extract_summary_line()` 方法用 regex `r"^\*\*[^*]+\*\*:\s*(.+)$"` 提取 summary 第一行。0.4.7 后 LLM 输出的 summary 格式变多（含 `#` 标题、`---` 分隔线、空白行），regex 匹配失败导致 abstract 返回空字符串或错误内容。

### 改动

在 `_extract_summary_line()` 方法中，把 regex 匹配改为逐行扫描：

```python
# 原：用 regex 匹配 **Title**: content 格式
# 改：逐行扫描，跳过空白行、# 标题、--- 分隔线
for line in summary.split("\n"):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("---"):
        continue
    if len(stripped) > 3:
        return stripped[:200]

# Fallback：去掉开头的 # 标记
first_line = summary.split("\n")[0].strip().lstrip("#").strip()
return first_line if first_line else ""
```

## 升级时如何重打

两处修改在 session.py 的不同方法里，互不冲突。找到对应方法名，按上述说明手动改。如果新版本在这两个方法附近有大量重构，重点保住 ROOT context（修改 A）——这是 extract 正常工作的必要条件。

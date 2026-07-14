# commit-compaction-init-params

## Summary
修复 compaction/commit 时 `SessionExtractContextProvider.__init__()` 报 `TypeError: got an unexpected keyword argument 'include_tool_parts_in_conversation'` 导致 compaction 失败的问题。

## Root Cause
`compressor_v3.py` 在实例化 `SessionExtractContextProvider` 时传入了 `include_tool_parts_in_conversation=True`，但该类的 `__init__` 没有接收这个参数，也没有接收 `split_long_text_messages_for_extraction` 参数。每次触发 compaction 都直接 TypeError，完全没执行就炸了。

注意：这两个参数虽然已定义为 class attributes（默认值），但未在 `__init__` 中声明接收，导致调用方传参时报错。修复后在 `__init__` 中接收并赋值，保持向后兼容（默认值不变）。

## Affected Versions
- OV 0.4.8: 已存在此 bug
- OV 0.4.9: 仍存在
- OV 0.4.5: 未确认（compressor_v3.py 不存在）

## Changed File
`server/openviking/session/memory/session_extract_context_provider.py`

## Lines Changed
在 `__init__` 签名中加入两个参数 + 在 body 中赋值：+4 lines

## Verification
修复后 OV server 重启，compaction 不再抛 TypeError。

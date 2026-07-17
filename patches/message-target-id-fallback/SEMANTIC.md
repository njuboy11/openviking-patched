# Patch: message-target-id-fallback

## 影响文件
- `server/openviking/session/memory/memory_isolation_handler.py`

## 问题
`_message_target_id()` 对 assistant 消息（有 peer_id 但不是 peer owner）直接返回 None，导致 events 类型的 `read_message_ranges()` 在解析 LLM 给出的合法 ranges（如 "213-242"）时，每个消息的 target_id 都为 None → `_range_targets` 收到 0 个 target → `calculate_memory_uris()` 返回空 → 被 e8a515d 的 skip-and-warn 兜底丢弃。

**根因链路**：
1. LLM 根据 chat 索引生成 ranges（如 "213-242"，完全在 244 条消息内）
2. `read_message_ranges()` 对每个 msg 调用 `_message_target_id(msg)`
3. assistant 消息有 peer_id 但 `_is_peer_owner_message()` 返回 False
4. `if raw_peer_id in (None, "")` 不匹配（有值），直接 return None
5. target_ids 全部被 silent drop → 0 targets → empty URIs

## 修改
在 `_message_target_id()` 中增加一层 fallback：当消息有 peer_id 且 allow_self=True 时，返回 `_SELF_PEER_ID` 而非 None。

```python
# 原文
if raw_peer_id in (None, "") and self.allow_self:
    return _SELF_PEER_ID
return None

# 改为
if raw_peer_id in (None, "") and self.allow_self:
    return _SELF_PEER_ID
if peer_id and self.allow_self:
    return _SELF_PEER_ID
return None
```

## 与其他补丁的关系
- **c62c6d9** (schema guard)：防止 LLM 输出 page_id（已证实生效）
- **e8a515d** (skip-and-warn)：URIs 为空时 skip 而非 abort 整个 batch（兜底）
- **b01a1e0** (detailed warning)：在 `_range_targets` 加详细日志定位 ranges 越界（诊断）
- **本补丁**：根治——消息有 peer_id 但非 owner 时也能 resolve 出 target_id

## 升级时如何重打
```bash
cd /tmp/openviking-patched
git am patches/message-target-id-fallback/*.patch
cp server/openviking/session/memory/memory_isolation_handler.py /usr/local/lib/python3.12/dist-packages/openviking/session/memory/
systemctl restart openviking-server
```

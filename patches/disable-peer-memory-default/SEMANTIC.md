# disable-peer-memory-default

## What
Change `peer_enabled` default from `True` to `False` in `MemoryPolicy`.

## Why
OV 0.4.9+ introduced "peer memory" which writes **duplicate memories** — one to `user/main/memories/...` (self) and another to `user/main/peers/<peer_id>/memories/...` (peer).

In our single-user setup (鹏哥 + 二狗子飞书私聊), the peer path duplicates the self path for every events-type memory, which is wasteful and confusing. We don't use multi-user peer isolation.

## 0.4.10 Status Check (2026-07-18)
- **Live OV 0.4.10 server** `/usr/local/lib/python3.12/dist-packages/openviking/session/memory_policy.py:57`
  - 状态：`peer_enabled: bool = True` ← **0.4.10 自身未修复，本 patch 仍需应用**
- **Fork HEAD** `server/openviking/session/memory_policy.py:57`
  - 状态：`peer_enabled: bool = False` ← 已 patched（a0d4f3a 引入）

## How
One-line change in `openviking/session/memory_policy.py:57`:

```diff
- peer_enabled: bool = True
+ peer_enabled: bool = False
```

## Live Apply (2026-07-18 16:35 CST)
```bash
# 备份
cp /usr/local/lib/python3.12/dist-packages/openviking/session/memory_policy.py \
   /usr/local/lib/python3.12/dist-packages/openviking/session/memory_policy.py.bak-pre-disable-peer-20260718

# 应用
sed -i 's/    peer_enabled: bool = True$/    peer_enabled: bool = False/' \
  /usr/local/lib/python3.12/dist-packages/openviking/session/memory_policy.py

# 重启 OV service
systemctl restart openviking-server

# 验证
curl http://127.0.0.1:1933/health
grep 'peer_enabled' /usr/local/lib/python3.12/dist-packages/openviking/session/memory_policy.py
```

## Impact
- All new sessions: no peer memory written (clean single-path)
- Existing sessions with `memory_policy: null` in `.meta.json`: also affected (null → pick up new default)
- Can be overridden per-session via API `memory_policy: {peer: {enabled: true}}` if ever needed
- Does NOT affect `self_enabled` — self memory continues normally
- Does NOT affect existing peer memory files already written

## Verification
- [ ] Live `memory_policy.py:57` = `peer_enabled: bool = False`
- [ ] `/health` 返回 200
- [ ] 新 session commit 后，文件系统只有 `user/main/memories/...`，没有 `user/main/peers/.../memories/...`
- [ ] journalctl 无 `peer_enabled` 相关 warning
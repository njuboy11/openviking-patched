# Disable Peer Memory Default

## What 
Change `peer_enabled` default from `True` to `False` in `MemoryPolicy`.

## Why
OV 0.4.9+ introduced "peer memory" which writes **duplicate memories** — one to `user/main/memories/...` (self) and another to `user/main/peers/<peer_id>/memories/...` (peer). 

In our single-user setup (鹏哥 + 二狗子飞书私聊), the peer path duplicates the self path for every events-type memory, which is wasteful and confusing. We don't use multi-user peer isolation.

## How
One-line change in `openviking/session/memory_policy.py:57`:

```python
# before
peer_enabled: bool = True

# after  
peer_enabled: bool = False
```

## Impact
- All new sessions: no peer memory written (clean single-path)
- Existing sessions with `memory_policy: null` in `.meta.json`: also affected (null → pick up new default)
- Can be overridden per-session via API `memory_policy: {peer: {enabled: true}}` if ever needed
- Does NOT affect `self_enabled` — self memory continues normally
- Does NOT affect existing peer memory files already written

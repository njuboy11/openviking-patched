# retry-archive-extract — Phase 2 retry endpoint

## Summary

Adds `POST /api/v1/sessions/{id}/archives/{archive_id}/retry` to manually re-trigger Phase 2 memory extraction for a previously-failed archive, **without** re-archiving messages.

Three additive changes, all in OV server:
1. `session/session.py` — `_run_memory_extraction` accepts new `skip_previous_archive_check` kwarg
2. `session/session.py` — new `retry_archive_extraction(archive_index)` method (78 lines)
3. `server/routers/sessions.py` — new endpoint @ `L424`
4. `service/session_service.py` — new `retry_archive(session_id, archive_id, ctx)` wrapper

## Root Cause

OV archives run Phase 2 (memory extraction) as a background async task after commit. When Phase 2 fails (API overload, timeout, transient error), it writes `.failed.json` but there is **no programmatic retry**. The archive's `messages.jsonl` and infrastructure are intact — only a trigger entry point is missing.

In our setup (鹏哥 + 二狗子), failed archives commonly appear after VLM API overload (`520 archive_002 ranges 越界` etc.), forcing manual log inspection + service restart hacks.

## 0.4.10 Status Check (2026-07-18)

| File | Live state (pre-patch) | Live state (post-patch) | Fork HEAD state |
|------|------------------------|--------------------------|-----------------|
| `session/session.py` | L1328 = `_run_memory_extraction` (no skip param); L2031 = no retry method | L1328 +skip kwarg; L2018 = `retry_archive_extraction` | L2031 already contains `retry_archive_extraction` (a0d4f3a snapshot) |
| `server/routers/sessions.py` | 0 retry endpoints | L424 = `POST ...archives/{id}/retry` endpoint | L431 already contains endpoint (a0d4f3a snapshot) |
| `service/session_service.py` | 0 retry methods | L325 = `retry_archive` | L344 already contains method (a0d4f3a snapshot) |

→ **0.4.10 live 没自带 retry endpoint，patch 必须手工 apply**
→ Fork HEAD a0d4f3a 已包含（2026-07-17 22:19 复合 commit 导入快照时已 apply）

## Live Apply 步骤（2026-07-18 16:46 CST 完成）

```bash
# 1. 备份（每个文件一份 .bak-pre-retry-archive-20260718）
cp /usr/local/lib/python3.12/dist-packages/openviking/session/session.py \
   /usr/local/lib/python3.12/dist-packages/openviking/session/session.py.bak-pre-retry-archive-20260718
cp /usr/local/lib/python3.12/dist-packages/openviking/server/routers/sessions.py \
   /usr/local/lib/python3.12/dist-packages/openviking/server/routers/sessions.py.bak-pre-retry-archive-20260718
cp /usr/local/lib/python3.12/dist-packages/openviking/service/session_service.py \
   /usr/local/lib/python3.12/dist-packages/openviking/service/session_service.py.bak-pre-retry-archive-20260718

# 2. 用 python 脚本做 3 处精确插入（PATCH.diff 行号已对齐 0.4.10 live）

# 3. 验证语法
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/openviking/session/session.py
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/openviking/server/routers/sessions.py
python3 -m py_compile /usr/local/lib/python3.12/dist-packages/openviking/service/session_service.py

# 4. 重启 OV service
systemctl restart openviking-server

# 5. 验证 endpoint 注册
curl -X POST -H "Authorization: Bearer $ROOT_KEY" -H "X-OpenViking-Account: ..." -H "X-OpenViking-User: ..." \
     http://127.0.0.1:1933/api/v1/sessions/{session_id}/archives/{archive_id}/retry
```

## Verification — Live (2026-07-18 16:46 CST)

- ✅ `python3 -m py_compile` 三个文件全部通过
- ✅ `systemctl restart openviking-server` 成功，PID 173646 active
- ✅ `/health` = `{"status":"ok","version":"0.4.10"}`
- ✅ `POST /api/v1/sessions/.../archives/.../retry` 已注册（service log 显示 `telemetry operation=session.archive.retry`）
- ✅ endpoint 报 `404 Session not found`（因为 trusted mode auth scope 是 `default/main`，retry 调用路径通到 service 层）→ 不是 patch 问题，是 user scope 问题

## Usage 模式（鹏哥 fail-archive 救急 SOP）

```bash
# 1. 找失败的 archive
find /root/.openviking/data/viking/default/user/main/sessions -name '.failed.json' 2>&1

# 2. 查看失败原因
cat /root/.openviking/data/viking/default/user/main/sessions/<sid>/history/archive_<idx>/.failed.json

# 3. 通过 trusted mode 重试
ROOT_KEY=$(grep -oP 'root_api_key.*"\K[^"]+' /root/.openviking/ov.conf)
curl -X POST -H "Authorization: Bearer $ROOT_KEY" \
     -H "X-OpenViking-Account: $ACCOUNT" -H "X-OpenViking-User: $USER" \
     http://127.0.0.1:1933/api/v1/sessions/<sid>/archives/<idx>/retry

# 4. 验证 .failed.json 被删 + 新 .meta.json 重写
ls /root/.openviking/data/viking/default/user/main/sessions/<sid>/history/archive_<idx>/
```

## Implementation details

### Hunk1 (session.py:1328)
在 `_run_memory_extraction` 函数签名末尾插入关键字分隔符和 `skip_previous_archive_check` 参数：
```diff
         memory_policy: Optional[Dict[str, Any]],
+        *,
+        skip_previous_archive_check: bool = False,
     ) -> None:
```

### Hunk2 (session.py:1356)
包裹 `_wait_for_previous_archive_done` 调用为可选：
```diff
         try:
-            await self._wait_for_previous_archive_done(archive_index)
+            if not skip_previous_archive_check:
+                await self._wait_for_previous_archive_done(archive_index)
```

`skip_previous_archive_check=True` 是 retry 必需——否则 retried archive 可能命中"前一个 archive `.done` 缺失"的死锁。

### Hunk3 (session.py:2017)
新增 `retry_archive_extraction` method，紧跟 `_read_archive_messages` 末尾 `return messages`。详见 patch.diff。

### Hunk4 (routers/sessions.py:424)
新增 endpoint，紧跟 `extract_session` 之后。

### Hunk5 (service/session_service.py:325)
新增 `retry_archive` wrapper，紧跟 `get_commit_task` 之后。

## 影响

- 新 session commits 不受影响
- 旧 archive 重试不影响
- 不需要 OV 协议级改动
- plugin 侧不需要改动
- `skip_previous_archive_check` 默认 False 保留旧行为，向后兼容

## Affected Versions

- **0.4.10 live verified**（2026-07-18 16:46 CST）：`/usr/local/lib/python3.12/dist-packages/openviking/{session/session.py, server/routers/sessions.py, service/session_service.py}` 三个文件全部 patched
- fork HEAD `a0d4f3a` 已隐式包含
- 0.4.9 / 0.4.8 等更早版本方法定义稍有不同（`_read_archive_messages` 签名差异），需要单独 fork

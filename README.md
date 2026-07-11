# OpenViking Patched

Self-maintained fork of [volcengine/OpenViking](https://github.com/volcengine/OpenViking). Based on v0.4.8 with our accumulated patches. Not tracking upstream — we maintain our own branch going forward.

## Why

Upstream is a large multi-tenant codebase. Many of our bugfixes are specific to our deployment (trusted auth mode, OpenClaw plugin, self-hosted Qdrant). PRs sit open for weeks. We need our own stable baseline.

## Repo Structure

```
server/openviking/   → Full server source (v0.4.8 + all patches applied)
plugin/openviking-plugin/ → OpenClaw plugin source (extension code)
patches/             → Individual .patch files, one per fix
```

## Patch Inventory (11 PRs, 9 Issues)

### Active Patches (applied, not in upstream v0.4.8)

| # | Patch | PR | File | Scope |
|---|-------|-----|------|-------|
| 1 | `models-rerank-openai_rerank.py.patch` | [#2619](https://github.com/volcengine/OpenViking/pull/2619) | `openai_rerank.py` | Filter empty docs before rerank API call |
| 2 | `storage-viking_fs.py.patch` | [#2927](https://github.com/volcengine/OpenViking/pull/2927) | `viking_fs.py` | Concurrent `read_batch` via `asyncio.gather` |
| 3 | `retrieve-hierarchical_retriever.py.patch` | [#3135](https://github.com/volcengine/OpenViking/pull/3135) | `hierarchical_retriever.py` | Restore L2 document-level hits in global search |
| 4 | `session-session.py.patch` | [#3137](https://github.com/volcengine/OpenViking/pull/3137) / [#3172](https://github.com/volcengine/OpenViking/pull/3172) | `session.py` | Extract real abstract + Role.ROOT for peer isolation |
| 5 | `session-memory-memory_updater.py.patch` | [#3143](https://github.com/volcengine/OpenViking/pull/3143) | `memory_updater.py` | Use VLM summary as Qdrant abstract |

### Merged Upstream (already in v0.4.8, kept for reference)

| # | PR | Scope |
|---|-----|-------|
| 6 | [#2748](https://github.com/volcengine/OpenViking/issues/2748) | `str(ctx.role)` fixes (9 files) |
| 7 | [#2753](https://github.com/volcengine/OpenViking/pull/2753) | StreamHandler → QueueHandler |
| 8 | [#2481](https://github.com/volcengine/OpenViking/pull/2481) | Plugin: structured toolCall part |
| 9 | [#2491](https://github.com/volcengine/OpenViking/pull/2491) | Plugin: merge concurrent auto-recall calls |

### Open PRs (pending upstream, already applied locally)

| # | PR | Scope |
|---|-----|-------|
| 10 | [#2476](https://github.com/volcengine/OpenViking/pull/2476) | Force commit to skip blocked archives |
| 11 | [#2926](https://github.com/volcengine/OpenViking/pull/2926) | Rerank empty docs (superseded by #2619) |

### Open Issues (investigated, fixed or documented)

- [#3171](https://github.com/volcengine/OpenViking/issues/3171) — Peer isolation blocks extract in trusted mode
- [#3142](https://github.com/volcengine/OpenViking/issues/3142) — Abstract uses full content instead of VLM summary
- [#3136](https://github.com/volcengine/OpenViking/issues/3136) — Abstract returns markdown heading
- [#3134](https://github.com/volcengine/OpenViking/issues/3134) — Search returns 90% fewer results
- [#2989](https://github.com/volcengine/OpenViking/issues/2989) — Search ranks raw messages.jsonl above real memories

## Apply a Patch

```bash
cd /usr/local/lib/python3.12/dist-packages/openviking
patch -p1 < patches/session-session.py.patch
```

## Upgrade Notes

When upgrading pip package, re-apply all patches:

```bash
pip install openviking==<version>
for p in patches/*.patch; do patch -p1 -d /usr/local/lib/python3.12/dist-packages/openviking < $p; done
systemctl --user restart openviking-server
```

## License

Same as upstream OpenViking.

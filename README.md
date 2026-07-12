# OpenViking Patched

自维护的 OpenViking 分叉。基于上游 v0.4.8 + 本地补丁，不再跟主仓库走。

## 仓库结构

```
server/openviking/   → 完整服务端代码（v0.4.8 + 全部 patch 已打入）
plugin/openviking-plugin/ → OpenClaw 插件代码
patches/             → 独立 .patch 文件，每个修复一个
```

## 本地补丁清单

### 近期活跃 PR（2026-07-10 ~ 07-12 提的）

| PR | 文件 | 修复内容 |
|----|------|----------|
| [#3135](https://github.com/volcengine/OpenViking/pull/3135) | `hierarchical_retriever.py` | 恢复 L2 文档级召回命中（0.4.7 回归导致结果少 90%） |
| [#3137](https://github.com/volcengine/OpenViking/pull/3137) | `session.py` | abstract 提取跳过 markdown 标题，返回真实文本 |
| [#3143](https://github.com/volcengine/OpenViking/pull/3143) | `memory_updater.py` | Qdrant abstract 用 VLM 生成的 summary 而非全文 |
| [#3172](https://github.com/volcengine/OpenViking/pull/3172) | `session.py` | extract 阶段用 Role.ROOT 绕过 trusted 模式 peer 隔离 |
| [#N/A](https://github.com/njuboy11/openviking-patched) | `context-lifecycle-service.js` | assemble fallback 加 token 预算裁剪（20%），防 context overflow |

### 早期补丁（已在本地生效，上游 Open 或已关）

| PR | 文件 | 修复内容 |
|----|------|----------|
| [#2476](https://github.com/volcengine/OpenViking/pull/2476) | `session.py` | 强制 commit 跳过卡死的 archive |
| [#2619](https://github.com/volcengine/OpenViking/pull/2619) | `openai_rerank.py` | rerank 前过滤空文档 |
| [#2753](https://github.com/volcengine/OpenViking/pull/2753) | `logger.py` | StreamHandler → QueueHandler 防死锁 |
| [#2927](https://github.com/volcengine/OpenViking/pull/2927) | `viking_fs.py` | `read_batch` 并发 via `asyncio.gather` |

### 上游已合入（v0.4.8 已包含）

- [#2748](https://github.com/volcengine/OpenViking/issues/2748) — 全局 `str(ctx.role)` 替换（9 个文件）
- [#2481](https://github.com/volcengine/OpenViking/pull/2481) — Plugin: 结构化 toolCall 替换文本占位符
- [#2491](https://github.com/volcengine/OpenViking/pull/2491) — Plugin: 合并并发 auto-recall 调用

## 应用补丁（升级后恢复）

```bash
cd /usr/local/lib/python3.12/dist-packages/openviking
for p in patches/*.patch; do
  patch -p1 < $p
done
```

## License

同上游 OpenViking。

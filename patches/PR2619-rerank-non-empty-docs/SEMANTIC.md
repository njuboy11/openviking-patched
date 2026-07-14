# PR2619 — Rerank 空文档过滤

## 影响文件
`openviking/models/rerank/openai_rerank.py` — `rerank()` 方法

## 问题
SiliconFlow 等 rerank provider 提交空字符串文档时会被无声丢弃，返回的 results 数量对不上原始 documents 数量，导致 `results[index]` 越界崩溃。

## 修改

在 `rerank()` 方法开头插入空文档过滤逻辑：

1. 遍历 `documents`，跳过空字符串，保留到 `non_empty_docs[]`
2. 同时记录 `non_empty_indices[]` 保存原始 index 映射
3. 如果所有文档都是空的 → 直接 return `[0.0] * len(documents)`
4. 后续 `model`、`top_n`、`token_usage`、结果映射全部改用 `non_empty_docs`
5. 最终用 `non_empty_indices` 把 API 返回的 results map 回原始 `documents[]` index

## 在 0.4.9 上的状态

0.4.9 新增了 `fix(rerank): accept sparse indexed results (#3121)` — 修复了空文档问题的一个子集（sparse indexed results），**但未处理空字符串过滤**。PR2619 仍需。

## 升级时如何重打

找到 `async def rerank(self, model: str, query: str, documents: List[str])` 方法，在 `documents` 遍历之前加入上述过滤逻辑。与 0.4.9 的 #3121 改动无冲突（#3121 改的是结果 `index` 字段处理，PR2619 改的是输入过滤）。

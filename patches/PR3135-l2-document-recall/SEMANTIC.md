# PR3135 — L2 文档级召回恢复

## 影响文件
`openviking/retrieve/hierarchical_retriever.py` — 全局检索阶段

## 问题
0.4.7 重构导致全局搜索只召回 L0/L1（目录级），不再包含 L2（文档级）命中。结果数减少 ~90%，auto-recall 几乎废掉。

## 修改

1. level filter 条件化：当外部未指定 level 时，全局搜索用 `level=[0, 1, 2]`（包含 L2）；当已指定时仍用 `level=[0, 1]`
2. 增加 L2 fallback：全局搜索返回的 L2 文档命中被纳入 `initial_candidates[]`，参与后续递归搜索和评分

## 在 0.4.9 上的状态

0.4.9 新增了 image search 功能（#3093），在同一个文件里。PR3135 的改动和 #3093 无冲突。

## 升级时如何重打

找到 `level=[0, 1]` 那一行（在 `async def _global_search` 附近），改为条件 `level=[0, 1, 2] if level is None else [0, 1]`。再在 result 遍历循环后加 L2 document 的 `initial_candidates` append 逻辑。

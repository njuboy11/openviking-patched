# vectors_l2_only — 重索引跳过 L0/L1

## 影响文件
`openviking/service/reindex_executor.py`

## 修改

新增 `vectors_l2_only` 重索引模式：

1. `SUPPORTED_MODES_BY_TYPE` 每个类型加 `"vectors_l2_only"` 模式
2. 调用入口设置 `self._skip_l0_l1 = (mode == "vectors_l2_only")`
3. 文件扫描阶段：如果 `_skip_l0_l1`，跳过目录级 L0/L1 向量化（`deduped_directories = []`）
4. 每条记录处理时：如果 `_skip_l0_l1`，直接跳到 `{uri}/SKILL.md` 做 L2 文档级向量化

**用途**：技能目录已建立索引，不需要重新做目录级向量化，只更新 SKILL.md 文档向量即可。

## 在 0.4.9 上的状态

reindex_executor.py 在 0.4.9 零改动，直接 copy 即可。

## 升级时如何重打

直接用备份文件覆盖，或从仓库取上次保存的版本。

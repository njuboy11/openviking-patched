# vectors_l2_only — 重索引跳过 L0/L1

## 影响文件
`openviking/service/reindex_executor.py`

## 问题
重新索引技能时，默认流程会先做目录级向量化（L0/L1），再做 SKILL.md 文档级向量化（L2）。如果技能目录已经建立过索引、只需要更新文档内容，这种全量重做是浪费。

## 修改

新增 `vectors_l2_only` 重索引模式，跳过目录级 L0/L1 直接到 SKILL.md L2：

### 1. 注册新模式
在 `SUPPORTED_MODES_BY_TYPE` 字典里，每个类型的 value set 加 `"vectors_l2_only"`：
```python
"memory": {"vectors_only", "semantic_and_vectors", "vectors_l2_only"},
# 对 global_namespace / user_namespace / skill_namespace / resource / skill 同样加
```

### 2. 设置跳过标志
在 `execute()` 方法中，开始处理前：
```python
self._skip_l0_l1 = (mode == "vectors_l2_only")
```

### 3. 文件扫描跳过目录
在 `_collect_files()` 方法中，收集文件后：
```python
if self._skip_l0_l1:
    deduped_directories = []  # 清空，不处理目录级
```

### 4. 每条记录直接走 L2
在 `_process_one_record()` 方法中，如果 `_skip_l0_l1`：
```python
# 直接读 {uri}/SKILL.md 做文档级 L2 向量化
skill_file_uri = f"{uri}/SKILL.md"
skill_content = await self._safe_read_text(skill_file_uri)
await self._upsert_context(
    uri=skill_file_uri,
    abstract=skill_content[:200],
    vector_text=skill_content,
    level=ContextLevel.DETAIL,  # L2
    ...
)
```

## 升级时如何重打

找到 `SUPPORTED_MODES_BY_TYPE`（类属性开头），加 mode；找到 `execute()`，加 `_skip_l0_l1` 设置；找到 `_collect_files()`，加清空逻辑；找到 `_process_one_record()`，加 SKILL.md 直接处理分支。如果新版本重构了 `ReindexExecutor` 类结构，可能需要调整插入位置，但逻辑不变。

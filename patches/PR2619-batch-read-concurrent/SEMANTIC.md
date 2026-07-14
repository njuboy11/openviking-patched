# PR2619 — read_batch 并发优化

## 影响文件
`openviking/storage/viking_fs.py` — `read_batch()` 方法 + typing import

## 修改

1. `from typing import ...` 行加 `Tuple`
2. `read_batch()` 方法：串行 for 循环 → `asyncio.gather` 并发

```
原: for uri in uris: content = await self.abstract()  # 串行
改: tasks = [_read_one(uri) for uri in uris]; await asyncio.gather(*tasks)  # 并发
```

内部新增 `_read_one()` 辅助函数，每个 URI 独立读取，异常返回空字符串。

## 在 0.4.9 上的状态

0.4.9 在 viking_fs.py 里新增了 image search 功能（`find()` 加 `image_url` 参数，#3093）。**这些新代码和 PR2619 的 read_batch 改动不冲突**——两个改动在不同方法里，互不影响。

## 升级时如何重打

1. 备份 0.4.9 官方 `viking_fs.py`
2. typing import 行手动加 `Tuple`
3. 找到 `async def read_batch(` 方法，整个方法体替换为并发版本
4. 不要用机械 diff 或 patch 工具——必须手动改，避免把 find() 的 image_url 参数吃掉了

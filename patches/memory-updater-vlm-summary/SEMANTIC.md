# VLM Summary 优先

## 影响文件
`openviking/session/memory/memory_updater.py`

## 修改

在 `_vectorize_uri()` 方法中，abstract 提取逻辑：

```
原: abstract = LinkRenderer.strip_all_links(mf.content or "")
改: abstract = mf.extra_fields.get("summary", "") or LinkRenderer.strip_all_links(mf.content or "")
```

**原因**：VLM 生成的 summary（存在 `extra_fields.summary`）比全文 strip links 更精准。优先取 VLM summary，fallback 到全文。

## 在 0.4.9 上的状态

memory_updater.py 在 0.4.9 零改动，直接 copy 即可。

## 升级时如何重打

直接用备份文件覆盖，或手动改一行。

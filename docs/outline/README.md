# Outline 目录索引（项目内维护）

## 目的

Outline 的文档目录结构（例如“待办任务”目录）在日常自动化写入时会被频繁使用。每次都通过 API 全量查询目录树会慢、且容易因为同名文档造成歧义。

因此在仓库内维护一个**不含密钥**的目录索引文件：

- `docs/outline/outline-index.json`

后续脚本/技能可以**优先使用该索引定位目标文档 id**，并在执行写入/归档前用 `documents.info` 做一次轻量校验（确认 title/collectionId/parentDocumentId 未漂移）。

## 安全约束（强制）

- **不要**把 `OUTLINE_API_KEY` 写进仓库
- 索引文件只允许包含：`collectionId`、文档 `id/title/url/parentDocumentId/updatedAt/archivedAt` 等元数据

## 刷新索引

在项目根目录配置好 `.env` 后执行：

```bash
set -a && source .env && set +a
python scripts/outline_refresh_index.py
```

输出会给出：collection 信息、抓取到的文档数量、根目录标题列表、以及可能的“同父级重名”冲突提示。

## 使用建议（给技能/脚本）

- **优先**读取 `docs/outline/outline-index.json`，按 `paths`（如 `待办任务/待办清单（汇总）`）或按 `nodes` 条件筛选定位目标
- **执行前必做**：对目标文档 id 调 `documents.info` 校验存在性与关键字段
- 若校验失败（被移动/重命名/归档），再回退到 `documents.list + documents.search` 进行全量定位，并在成功后刷新索引


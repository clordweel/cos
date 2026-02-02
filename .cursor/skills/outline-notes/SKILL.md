---
name: outline-notes
description: 连接并管理私有部署 Outline 笔记（collections、documents、search）。使用环境变量 OUTLINE_BASE_URL 与 OUTLINE_API_KEY（存本地 .env，不提交）通过 HTTP API 调用常用 endpoints：collections.list / documents.list / documents.search / documents.info / documents.create / documents.update。用于“同步笔记、检索、创建/更新 Outline 文档”的场景。
---

# Outline（私有部署）笔记连接与管理

## 前置约定（本项目）

在项目根目录本地 `.env`（不提交）配置：

- `OUTLINE_BASE_URL`（例如：`https://outline.junhai.work`）
- `OUTLINE_API_KEY`（例如：`ol_api_...`）
- `OUTLINE_DEFAULT_COLLECTION`（默认文档集名称，例如：`COS 文档`）

加载环境变量：

```bash
set -a && source .env && set +a
```

## 鉴权方式

- Header：`Authorization: Bearer $OUTLINE_API_KEY`
- `Content-Type: application/json`

注意：若你的 `.env` 里存在包含空格的值（例如 `FAC_AUTH_HEADER`），必须使用引号包裹，确保 `source .env` 不会把它当成命令执行。

## 常用操作（curl 模板）

> Outline API 通常使用“动作式 endpoints”，路径形如 `/api/<resource>.<action>`。

### 1) 列出知识库（Collections）

```bash
curl -sS "$OUTLINE_BASE_URL/api/collections.list" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limit": 20, "offset": 0}'
```

### 2) 列出某个知识库下的文档（Documents）

将 `<collectionId>` 替换为 collections.list 返回的 id：

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.list" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collectionId": "<collectionId>", "limit": 20, "offset": 0}'
```

### 3) 搜索文档

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.search" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "关键词", "limit": 20, "offset": 0}'
```

### 4) 获取文档详情（info）

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.info" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": "<documentId>"}'
```

### 5) 创建文档

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.create" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collectionId": "<collectionId>",
    "title": "标题",
    "text": "# 内容（Markdown）",
    "publish": true
  }'
```

### 6) 更新文档（覆盖式）

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.update" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "<documentId>",
    "title": "新标题（可选）",
    "text": "# 新内容（Markdown）",
    "publish": true
  }'
```

### 7) 将草稿直接发布

当发现文档处于草稿（例如 `publishedAt` 为空）时，可直接：

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.update" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "<documentId>",
    "publish": true
  }'
```

## 默认文档集（COS 文档）

若任务说明“默认文档集为 COS 文档”，则优先使用 `.env` 中的：

- `OUTLINE_DEFAULT_COLLECTION="COS 文档"`

并通过 `collections.list` 找到对应 `collectionId` 后再进行 `documents.create`。

## 推荐：在项目内维护目录索引（减少重复查询）

如果你希望免去每次全量查询目录树的步骤，可以在仓库内维护一个**不含密钥**的目录索引文件：

- `docs/outline/outline-index.json`

并用脚本定期刷新（读取本地 `.env`）：

```bash
set -a && source .env && set +a
python scripts/outline_refresh_index.py
```

后续任何“新增/追加/归档/迁移”操作都可以：

- **优先**从索引里按 `paths`（例如 `待办任务/待办清单（汇总）`）定位目标文档 id
- **执行前仍必须**调用 `documents.info` 做轻量校验（确认 `collectionId/title/parentDocumentId/archivedAt` 等关键字段未漂移）
- 只有当索引缺失/校验失败时，才回退到全量 `documents.list + documents.search` 重新定位，并建议刷新索引

## 关键规则：执行前先确认已有的目录结构（强制）

默认文档集中通常已经有人按“目录文档（父文档）→ 子文档”的方式组织内容（例如已存在 `待办任务` 目录）。**任何新增/追加文档内容前，必须先查询并确认现有层级结构**，再决定是“更新已有文档”还是“在指定父文档下新建子文档”，避免重复创建同名文档导致目录混乱。

> 说明：当项目内已维护 `docs/outline/outline-index.json` 时，“查询结构”可优先通过索引完成；但对具体目标文档的写入/归档动作前，仍必须 `documents.info` 校验。

### 0) 查询默认文档集的根目录（用于定位“目录文档”）

先用 `collections.list` 获取 `<collectionId>`，再列出该知识库下的文档（默认返回根目录层级，具体以 Outline 部署为准）：

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.list" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collectionId": "<collectionId>", "limit": 100, "offset": 0}'
```

### 1) 定位目标目录文档（例如“待办任务”）

优先从根目录列表中直接找标题；若根目录较大或不确定层级，再使用 `documents.search`，并**务必**用 `documents.info` 二次确认：

- 文档确实属于目标 `collectionId`
- 其 `parentDocumentId` 是否符合预期（是否为根目录/是否位于某个目录下）

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.search" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "待办任务", "limit": 20, "offset": 0}'

curl -sS "$OUTLINE_BASE_URL/api/documents.info" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": "<documentId>"}'
```

### 2) 列出某个目录文档下的子文档（用于决定“更新 or 新建”）

拿到目录文档 id（例如 `<todoDirDocumentId>`）后，列出其子文档：

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.list" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collectionId": "<collectionId>", "parentDocumentId": "<todoDirDocumentId>", "limit": 100, "offset": 0}'
```

### 3) 写入策略（强制优先级）

- **优先更新**：如果目录下已存在目标文档（例如 `待办任务` 下的某个待办清单文档），使用 `documents.update` 追加内容（并做简单去重）。
- **再新建子文档**：只有在确认目录下不存在合适目标时，才在该目录（父文档）下 `documents.create` 新建子文档，并显式带上 `parentDocumentId`。

```bash
curl -sS "$OUTLINE_BASE_URL/api/documents.create" \
  -H "Authorization: Bearer $OUTLINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collectionId": "<collectionId>",
    "parentDocumentId": "<todoDirDocumentId>",
    "title": "标题",
    "text": "# 内容（Markdown）",
    "publish": true
  }'
```

## 输出与安全要求（强制）

- 不要在日志/回复中输出 `OUTLINE_API_KEY`
- 对 destructive 操作（delete/archive 等）必须先 `info` 确认目标
- 返回给用户时优先输出：文档标题、id、url（如 API 返回）与摘要，而不是整篇正文


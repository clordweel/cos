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

## 输出与安全要求（强制）

- 不要在日志/回复中输出 `OUTLINE_API_KEY`
- 对 destructive 操作（delete/archive 等）必须先 `info` 确认目标
- 返回给用户时优先输出：文档标题、id、url（如 API 返回）与摘要，而不是整篇正文


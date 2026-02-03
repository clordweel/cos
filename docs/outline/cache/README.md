# Outline 默认文档集 Cache

本目录为**默认文档集（COS 文档）**的本地缓存，用于：

- **拉取**：从 Outline API 拉取文档正文与元数据到本地
- **编辑**：在 cache 内修改文档内容（Markdown + YAML frontmatter）
- **单向推送**：确认无误后，将 cache 内容推送到 Outline（不覆盖未在 cache 中修改的字段）

## 约定（强制）

- **修改只在 cache 做**：Outline 上的变更不自动回写 cache，需重新执行拉取
- **推送前必须确认**：避免误覆盖线上文档；推送脚本可支持 dry-run 与白名单
- **不含密钥**：cache 与 manifest 不包含 `OUTLINE_API_KEY` 等敏感信息

## 目录结构

```
cache/
├── README.md           # 本说明
├── collection.json     # 文档集元数据（id / name / url）
├── manifest.json       # 文档清单：id ↔ path、父子关系、标题
├── documents/          # 按文档 id 存储的 .md 文件（或 _new_<slug>.md 表示未推送的新文档）
│   ├── <id>.md         # 已有文档：frontmatter(id, title, path, parentDocumentId, url, updatedAt) + body
│   └── _new_<slug>.md  # 新文档（待推送）：frontmatter 含 parentDocumentId、title，无 id
```

## 使用

### 拉取（Outline → cache）

在项目根目录执行：

```bash
set -a && source .env && set +a
python scripts/outline_pull_cache.py
```

会读取 `docs/outline/outline-index.json` 中的节点列表，逐个调用 `documents.info` 拉取正文并写入 `cache/documents/<id>.md`，并更新 `collection.json` 与 `manifest.json`。

### 推送（cache → Outline，单向）

确认 cache 中修改无误后：

```bash
set -a && source .env && set +a
python scripts/outline_push_cache.py
```

- 对 manifest 中已有 `id` 的文档：根据 cache 中的 `title` 与 body 调用 `documents.update`
- 对 `_new_*.md`：根据 frontmatter 的 `parentDocumentId`、`title` 与 body 调用 `documents.create`，成功后写入 `id` 并重命名为 `<id>.md`、更新 manifest

可选：`--dry-run` 仅打印将要执行的更新/创建，不实际调用 API；`--only <path>` 仅推送指定 path 的文档（例如 `--only "方案架构/系统集成架构（Frappe + FAC/MCP + 知识库）"` 或对新文档用 `--only "工程实现（落地细节）"`）。

---
name: fetch-item-groups
description: 获取物料组编号/名称列表（Item Group.name），默认取前 10 条。用于用户要求“获取/列出物料组编号、Item Group 列表、前 N 个物料组”等场景；提供 bench / MCP(FAC) / REST / Python 多种通用取数方式，并支持可选数量、排序与 filters（通常不需要手动提供 site）。
---

# 获取物料组编号（Item Group.name）

## 目标

从指定环境中读取 `Item Group` 的 `name` 列表（通常就是物料组编号/唯一标识）。

默认：取前 10 条、只返回 `name` 字段、按 `name asc` 排序。

## 默认环境约定（本项目）

- 开发环境默认域名：`cos-dev.junhai.work`
- 建议在项目根目录创建本地 `.env`（不提交，参考 `.env.example`），用于保存：
  - `FAC_MCP_URL`
  - `FAC_AUTH_HEADER`（Bearer 或 token）
- 若本机 `hosts` 将 `cos-dev.junhai.work` 指向 `127.0.0.1` 且 nginx 未启用 TLS：`FAC_MCP_URL` 必须使用 **http** 协议

## 可配置参数（保持通用）

- `SITE`：站点名（bench 场景**通常可省略**；仅在 bench 未配置默认 site 或多站点时显式指定）
- `LIMIT`：返回数量（默认 10）
- `ORDER_BY`：排序（默认 `name asc`）
- `FILTERS`：可选过滤（保持只读查询）
  - 示例：只取启用的物料组：`{"is_group": 1}`（具体字段以你系统为准）

## 方式 A（推荐）：bench + frappe.client.get_list

### 1)（可选）确认 site 名称

优先用以下任一方式得到 site：

- `bench list-sites`
- 或查看 `sites/` 下的站点目录（排除 `assets/` 等非站点目录）

### 2) 拉取 Item Group 的 name

#### 2.1 默认 site 已配置（推荐写法：不传 `--site`）

```bash
cd "<PATH_TO_BENCH>" && \
bench execute frappe.client.get_list --kwargs '{
  "doctype": "Item Group",
  "fields": ["name"],
  "limit_page_length": <LIMIT>,
  "order_by": "<ORDER_BY>",
  "filters": <FILTERS>
}'
```

#### 2.2 多站点/无默认 site（显式指定 `--site`）

```bash
cd "<PATH_TO_BENCH>" && \
bench --site "<SITE>" execute frappe.client.get_list --kwargs '{
  "doctype": "Item Group",
  "fields": ["name"],
  "limit_page_length": <LIMIT>,
  "order_by": "<ORDER_BY>",
  "filters": <FILTERS>
}'
```

### 3) 输出格式

将返回的 JSON 数组提取为 `name` 列表并输出，例如：

- `All Item Groups`
- `...`

## 方式 B：REST API（已有会话或 Token 时）

当你有 Frappe 会话/Token 且可直接 HTTP 调用时，可使用资源接口（不同版本/部署可能略有差异，优先以实际为准）：

- `GET /api/resource/Item Group?fields=["name"]&limit_page_length=10&order_by=name%20asc`

注意：需要鉴权（cookie session / `Authorization` token），且权限由当前用户决定。

## 方式 C：MCP（推荐：FAC MCP / tools/call）

当你已接入 **Frappe Assistant Core (FAC)** 并能通过 MCP 调用工具时，优先走：

1) `tools/list`：确认存在 `list_documents` 工具，并查看其 `inputSchema`  
2) `tools/call`：调用 `list_documents` 获取 `Item Group` 的 `name`

### 示例 1：使用项目本地 .env（推荐）

```bash
set -a && source .env && set +a
curl -sS "$FAC_MCP_URL" \
  -H "Authorization: $FAC_AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_documents",
      "arguments": {
        "doctype": "Item Group",
        "fields": ["name"],
        "limit": 10
      }
    },
    "id": 1
  }'
```

说明：

- MCP 场景下 **不需要提供 site**（由 `$FAC_MCP_URL` 对应的站点决定）。
- 若要排序/过滤：按 `tools/list` 返回的 schema 支持项补充（例如 `order_by` / `filters` 等）。

## 方式 D：bench console / Python（适合快速验证）

在 bench console 中执行：

```python
import frappe
names = [d.name for d in frappe.get_all("Item Group", fields=["name"], limit=10, order_by="name asc")]
names
```

## 常见问题排查

- **返回空数组**：该站点可能未初始化物料组或无权限；确认站点与数据是否存在。
- **命令失败**：确认 `bench` 可用、`<PATH_TO_BENCH>` 正确；多站点时再补 `--site "<SITE>"`。
- **需要不同排序/过滤/字段**：调整 `fields` / `order_by` / `filters`；默认保持只读查询，避免 destructive 操作。


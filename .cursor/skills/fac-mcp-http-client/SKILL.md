---
name: fac-mcp-http-client
description: 通过 HTTP 直接调用 Frappe Assistant Core 的 MCP StreamableHTTP Endpoint（JSON-RPC 2.0）：如何发现 endpoint、完成 OAuth Bearer token 鉴权、调用 tools/list 与 tools/call、以及处理 401/403/参数校验错误。用于“需要直接操作 FAC MCP API / 走 HTTP 集成而非 Cursor 内置 MCP”的场景。
---

# FAC MCP（StreamableHTTP）HTTP 调用工作流

## 适用场景

- 需要从外部程序/脚本通过 HTTP 调用 FAC 的 MCP endpoint（不是 Cursor 的本地 MCP server）
- 需要用 `tools/list` / `tools/call` 远程操作 Frappe/ERPNext（权限与审计由 FAC 保证）

## 本项目默认开发域名与本地密钥存放

- 默认开发域名：`cos-dev.junhai.work`
- 建议在项目根目录使用本地 `.env`（不提交）管理：
  - 提交只保留 `.env.example`
  - `.env` 中可维护 `FAC_MCP_URL` 与 `FAC_AUTH_HEADER`
- 若本机 `hosts` 将 `cos-dev.junhai.work` 指向 `127.0.0.1` 且无 TLS/证书：`FAC_MCP_URL` 必须使用 **http** 协议

## Endpoint 与发现

- **OpenID discovery**：`GET /.well-known/openid-configuration`
  - 响应中包含 `mcp_endpoint`、OAuth endpoints、以及支持的协议版本
- **MCP endpoint**：`POST /api/method/frappe_assistant_core.api.fac_endpoint.handle_mcp`
  - 协议：JSON-RPC 2.0
  - 鉴权：OAuth 2.0 Bearer token（推荐）；FAC 也可能保留 legacy API Key 方案（视配置）

## 调用顺序（最小闭环）

1. **拿到 access_token**
   - 推荐走 OAuth Authorization Code + PKCE（FAC 文档有完整流程）
   - token 放在环境变量/安全存储中，严禁写入仓库

2. **initialize**
   - JSON-RPC：`method="initialize"`
   - 用于协商 `protocolVersion`

3. **tools/list**
   - JSON-RPC：`method="tools/list"`
   - 返回当前用户可用工具（已按权限过滤）

4. **tools/call**
   - JSON-RPC：`method="tools/call"`
   - 参数：`params.name`（工具名）+ `params.arguments`（工具输入）

## HTTP 请求要点

- Header：
  - `Authorization: Bearer <access_token>`（或 `Authorization: token <api_key>:<api_secret>`）
  - `Content-Type: application/json`
- Body：JSON-RPC 2.0 格式

## 快速示例（从 .env 读取默认 URL/Token）

前提：在项目根目录准备本地 `.env`（参考 `.env.example`），然后：

```bash
set -a && source .env && set +a
curl -sS "$FAC_MCP_URL" \
  -H "Authorization: $FAC_AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

## 失败处理（优先级）

- **401 Unauthorized**
  - token 缺失/过期/无效 → 重新走 token 获取或 refresh
- **403 / PermissionError**
  - 当前用户无 DocType/Tool 权限 → 换用户或调整权限/Tool requires_permission
- **-32602 Invalid params**
  - 对照 tool 的 `inputSchema` 修正字段名/类型/required
- **-32603 Internal error**
  - 去 Frappe error log / FAC audit log 定位；优先复现最小请求体

## 安全红线

- 不在日志/输出中暴露：token、api_secret、password、PII（除非用户明确授权且有脱敏策略）
- 任何 destructive 操作（delete/批量更新）都先做 list/get 确认目标与范围


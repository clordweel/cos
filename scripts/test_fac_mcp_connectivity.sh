#!/usr/bin/env bash
# 测试 FAC MCP 连通性
# 用法：从项目根目录执行 scripts/test_fac_mcp_connectivity.sh
# 依赖：.env 中配置 FAC_MCP_URL 与 FAC_AUTH_HEADER（或运行时 export）
#
# 若 .env 不在项目根，可指定路径，例如 bench 部署：
#   ENV_FILE=/home/frappe/frappe-bench/apps/cos/.env ./scripts/test_fac_mcp_connectivity.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
if [ -f "$ENV_FILE" ]; then
	set -a
	# shellcheck source=/dev/null
	source "$ENV_FILE"
	set +a
else
	echo "提示：未找到 $ENV_FILE（可设置 ENV_FILE 指定 .env 路径）"
fi

if [ -z "${FAC_MCP_URL:-}" ]; then
	echo "错误：未设置 FAC_MCP_URL。请在 .env 中配置或 export FAC_MCP_URL。"
	exit 1
fi
if [ -z "${FAC_AUTH_HEADER:-}" ]; then
	echo "错误：未设置 FAC_AUTH_HEADER。请在 .env 中配置或 export FAC_AUTH_HEADER。"
	exit 1
fi

echo "FAC MCP 连通性测试"
echo "Endpoint: $FAC_MCP_URL"
echo "---"

# 1. initialize（协商协议版本）
echo "1. 调用 initialize..."
INIT_RESP=$(curl -sS -w "\n%{http_code}" "$FAC_MCP_URL" \
	-H "Authorization: $FAC_AUTH_HEADER" \
	-H "Content-Type: application/json" \
	-d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}')
INIT_BODY=$(echo "$INIT_RESP" | head -n -1)
INIT_CODE=$(echo "$INIT_RESP" | tail -n 1)

if [ "$INIT_CODE" != "200" ]; then
	echo "   HTTP $INIT_CODE"
	echo "$INIT_BODY" | head -20
	echo ""
	echo "结论：FAC MCP 连通性失败（initialize 返回非 200）。"
	echo "  - 401：鉴权失败，请检查 FAC_AUTH_HEADER（token 是否有效/未过期）。"
	echo "  - 403：无权限。"
	echo "  - 其他：检查 FAC_MCP_URL 与站点/FAC 服务状态。"
	exit 1
fi
if echo "$INIT_BODY" | grep -q '"error"'; then
	echo "   JSON-RPC 错误："
	echo "$INIT_BODY" | head -5
	exit 1
fi
echo "   OK（HTTP 200）"

# 2. tools/list（列出可用工具）
echo "2. 调用 tools/list..."
LIST_RESP=$(curl -sS -w "\n%{http_code}" "$FAC_MCP_URL" \
	-H "Authorization: $FAC_AUTH_HEADER" \
	-H "Content-Type: application/json" \
	-d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}')
LIST_BODY=$(echo "$LIST_RESP" | head -n -1)
LIST_CODE=$(echo "$LIST_RESP" | tail -n 1)

if [ "$LIST_CODE" != "200" ]; then
	echo "   HTTP $LIST_CODE"
	echo "$LIST_BODY" | head -20
	echo ""
	echo "结论：initialize 通过，但 tools/list 失败。"
	exit 1
fi
if echo "$LIST_BODY" | grep -q '"error"'; then
	echo "   JSON-RPC 错误："
	echo "$LIST_BODY" | head -5
	exit 1
fi
echo "   OK（HTTP 200）"

# 可选：打印工具数量
TOOL_COUNT=$(echo "$LIST_BODY" | grep -o '"name"' | wc -l)
echo "   当前可用工具数量：$TOOL_COUNT"

# 3. 鉴权后获取当前用户信息（同一站点 Frappe API）
BASE_URL="${FAC_MCP_URL%/api/method/*}"
echo "3. 获取当前用户信息（$BASE_URL）..."
USER_RESP=$(curl -sS -w "\n%{http_code}" "$BASE_URL/api/method/frappe.auth.get_logged_user" \
	-H "Authorization: $FAC_AUTH_HEADER" \
	-H "Content-Type: application/json")
USER_BODY=$(echo "$USER_RESP" | head -n -1)
USER_CODE=$(echo "$USER_RESP" | tail -n 1)

if [ "$USER_CODE" != "200" ]; then
	echo "   HTTP $USER_CODE（无法获取当前用户，可能鉴权方式仅限 MCP 会话）"
	echo "   结论：FAC MCP 连通性正常；当前用户信息需通过 MCP 工具或其它 API 获取。"
	exit 0
fi
# Frappe 返回 {"message": "user@example.com"} 或 含 "exc" 的错误
LOGGED_USER=$(echo "$USER_BODY" | sed -n 's/.*"message"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
if [ -z "$LOGGED_USER" ]; then
	echo "   响应无法解析用户名："
	echo "$USER_BODY" | head -3
	echo "   结论：FAC MCP 连通性正常。"
	exit 0
fi
echo "   当前用户（login）：$LOGGED_USER"

# 拉取 User 文档（full_name、email 等）
USER_DOC_RESP=$(curl -sS -w "\n%{http_code}" "$BASE_URL/api/method/frappe.client.get" \
	-H "Authorization: $FAC_AUTH_HEADER" \
	-H "Content-Type: application/json" \
	-d "{\"doctype\":\"User\",\"name\":\"$LOGGED_USER\"}")
USER_DOC_BODY=$(echo "$USER_DOC_RESP" | head -n -1)
USER_DOC_CODE=$(echo "$USER_DOC_RESP" | tail -n 1)

if [ "$USER_DOC_CODE" = "200" ] && ! echo "$USER_DOC_BODY" | grep -q '"exc"'; then
	FULL_NAME=$(echo "$USER_DOC_BODY" | sed -n 's/.*"full_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	EMAIL=$(echo "$USER_DOC_BODY" | sed -n 's/.*"email"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	[ -n "$FULL_NAME" ] && echo "   姓名：$FULL_NAME"
	[ -n "$EMAIL" ] && echo "   邮箱：$EMAIL"
fi
echo ""
echo "结论：FAC MCP 连通性正常；当前用户：$LOGGED_USER"

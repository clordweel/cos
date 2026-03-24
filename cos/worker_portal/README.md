# COS Work - Worker Portal (React + shadcn)

Worker Portal 前端，使用 React + Vite + shadcn 风格组件，嵌入 Frappe 页面。

## Token 鉴权

使用 Bearer token 替代 cookies，解决 iOS WebView 下 cookie 不可靠问题。

- 登录：`POST /api/method/cos.worker_portal_api.login_for_token`，返回 `{ token, user }`
- 后续请求：`Authorization: Bearer wpt.<token>`
- Token 存于 localStorage，有效期 7 天（移动端 WebView 关闭后仍可保持登录）

Flutter 壳侧若以 **Token 为主**、Desk 允许站内重登的端到端约定，见主仓库：`docs/cos-mini-program-token-auth-plan.md`。

## 开发

```bash
pnpm install
pnpm dev
```

## 构建

```bash
pnpm build
```

输出到 `cos/public/worker_portal/`，由 Frappe 以 `/assets/cos/worker_portal/` 提供。

## 部署

构建产物 `cos/public/worker_portal/` 已加入 .gitignore，不再纳入版本控制。

- **本地**：首次 clone 或 pull 后执行 `cd cos/worker_portal && npm install && npm run build`
- **服务器**：`deploy_cos_to_dev.py` / `deploy_cos_to_prod.py` 会在 deploy 时自动执行 `npm install && npm run build`

## 功能

- **登录后跳转**：从未登录访问受保护页面（如审批）时，登录成功后会跳回原页面
- **SPA 路由**：工作台、审批、入库盘点均为 React 路由，无整页刷新

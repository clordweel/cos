# COS Work - Worker Portal (React + shadcn)

Worker Portal 前端，使用 React + Vite + shadcn 风格组件，嵌入 Frappe 页面。

## Token 鉴权

使用 Bearer token 替代 cookies，解决 iOS WebView 下 cookie 不可靠问题。

- 登录：`POST /api/method/cos.worker_portal_api.login_for_token`，返回 `{ token, user }`
- 后续请求：`Authorization: Bearer wpt.<token>`
- Token 存于 localStorage，有效期 7 天（移动端 WebView 关闭后仍可保持登录）

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

在 ai_cos_ops 根目录：

```bash
pnpm install   # 安装 workspace 依赖
cd vendor/cos/cos/worker_portal && pnpm build
```

然后按常规流程部署 cos 到 dev/prod。

## 功能

- **登录后跳转**：从未登录访问受保护页面（如审批）时，登录成功后会跳回原页面
- **SPA 路由**：工作台、审批、入库盘点均为 React 路由，无整页刷新

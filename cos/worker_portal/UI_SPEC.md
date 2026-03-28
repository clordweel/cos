# Worker Portal UI 规范

## 技术栈

- **组件**：以 **shadcn/ui**（Radix + `class-variance-authority` + Tailwind）为主，放在 `src/components/ui/`。
- **新页面**：优先组合现有 `Button` / `Card` / `Input` / `Label` / `Table` / `Badge`，避免裸写大量自定义 class。

## 布局

- **内容区**：使用 `WpPage`（`src/lib/wp-layout.tsx`）。默认 `max-w-2xl`、水平 `px-4`、上 `pt-4`、下 `pb-8`；表单/结果窄页传 `narrow` → `max-w-md`。
- **登录**：使用 `WpAuthPage`，内容 `max-w-md` 居中。
- **全屏短状态**（加载中、一行提示）：使用 `WpCentered`。
- **嵌入企业 App WebView**：不单独做浏览器式顶栏；标题由壳层导航栏承担。浏览器独立打开时可用 `WpPageTitle`（与 `isCosFlutterShell()` 组合）。

## 文字

- 正文说明：`text-sm leading-relaxed`；次要信息：`text-muted-foreground`。
- 一级页内标题（必要时）：`text-lg font-semibold tracking-tight`。
- 错误：`text-sm text-destructive`。

## 间距

- 区块之间：`space-y-4`（与 `WpPage` 默认一致）。
- 卡片内字段：`space-y-2` / `gap-2` grid。

## 禁止项

- 避免大段「操作说明」折叠块放在业务列表首屏；说明文档放 Outline / 内部 Wiki。
- 避免与壳层重复的 `border-b` 全宽顶栏（除非 `!isCosFlutterShell()` 且需要独立导航）。

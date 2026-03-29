import type { CSSProperties } from "react"

/** 与 Flutter `WeChatMiniProgramNavBar.barHeight` 对齐（供页面自定义时选用）。 */
export const COS_FLUTTER_SHELL_NAV_BAR_PX = 44

/**
 * 壳内顶留白：与 `cos_work_shell_inset.css` 中 `--cos-content-padding-top` 一致。
 * 固定定位 `top:`、paddingTop 等应共用此字符串，避免与 WpPage 回退不一致。
 * 其他文件勿再手写该 CSS 变量名：`npm run lint`（eslint.config.js）会报错。
 */
export const COS_SHELL_CONTENT_PADDING_TOP_CSS = `var(--cos-content-padding-top, calc(env(safe-area-inset-top, 0px) + ${COS_FLUTTER_SHELL_NAV_BAR_PX}px))`

/** 与 Flutter 壳 [MiniProgramRunnerScreen] 中 WebView User-Agent 约定一致。 */
export function isCosFlutterShell(): boolean {
	if (typeof navigator === "undefined") return false
	return /\bCosWorkApp\b/i.test(navigator.userAgent)
}

/**
 * 嵌入 Cos Work App WebView 时为主内容区顶留白。
 * 由 Frappe 模板 + cos_work_shell_inset.css 根据路径解析的 nav_bar_inset_mode 设置 `--cos-content-padding-top`；
 * safe_area 下变量多为 env(safe-area-inset-top)；此处仅消费变量；旧壳未带服务端样式时回退「安全区 + 44px」（偏保守）。
 */
export function cosFlutterShellContentInsetStyle(): CSSProperties | undefined {
	if (!isCosFlutterShell()) return undefined
	return {
		paddingTop: COS_SHELL_CONTENT_PADDING_TOP_CSS,
		boxSizing: "border-box",
	}
}

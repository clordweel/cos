import type { CSSProperties } from "react"

/** 与 Flutter `WeChatMiniProgramNavBar.barHeight` 对齐（供页面自定义时选用）。 */
export const COS_FLUTTER_SHELL_NAV_BAR_PX = 44

/** 与 Flutter 壳 [MiniProgramRunnerScreen] 中 WebView User-Agent 约定一致。 */
export function isCosFlutterShell(): boolean {
	if (typeof navigator === "undefined") return false
	return /\bCosWorkApp\b/i.test(navigator.userAgent)
}

/**
 * 嵌入 Cos Work App WebView 时为主内容区顶留白。
 * Flutter 注入 `--cos-content-padding-top`（由 DocType「壳内顶栏占位」决定：无 / 仅状态栏 / App 提供 / 页面自定义）。
 * 未注入时回退为「安全区 + 44px」以免旧壳全白。
 */
export function cosFlutterShellContentInsetStyle(): CSSProperties | undefined {
	if (!isCosFlutterShell()) return undefined
	return {
		paddingTop: `var(--cos-content-padding-top, calc(env(safe-area-inset-top, 0px) + ${COS_FLUTTER_SHELL_NAV_BAR_PX}px))`,
		boxSizing: "border-box",
	}
}

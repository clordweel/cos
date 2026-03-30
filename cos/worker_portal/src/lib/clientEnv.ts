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
 * safe_area 下变量为仅 env(safe-area-inset-top)（比 app_bar 少 44px）；旧壳未带服务端样式时回退「安全区 + 44px」（偏保守）。
 */
export function cosFlutterShellContentInsetStyle(): CSSProperties | undefined {
	if (!isCosFlutterShell()) return undefined
	return {
		paddingTop: COS_SHELL_CONTENT_PADDING_TOP_CSS,
		boxSizing: "border-box",
	}
}

/** 与 Cos Work App [CosThemeModeStore] / 首跳 `__cos_theme` 一致。 */
export type CosShellThemeMode = "light" | "dark" | "system"

let __cosShellThemeMediaListener: (() => void) | null = null

/** 设置 `html` 的 `.dark` 与 `data-cos-theme`；`system` 时监听系统深浅色。 */
export function applyCosShellThemeMode(mode: CosShellThemeMode): void {
	if (typeof document === "undefined") return
	const root = document.documentElement
	root.setAttribute("data-cos-theme", mode)
	if (__cosShellThemeMediaListener) {
		try {
			window
				.matchMedia("(prefers-color-scheme: dark)")
				.removeEventListener("change", __cosShellThemeMediaListener)
		} catch {
			/* ignore */
		}
		__cosShellThemeMediaListener = null
	}
	const computeDark = (): boolean => {
		if (mode === "dark") return true
		if (mode === "light") return false
		return window.matchMedia("(prefers-color-scheme: dark)").matches
	}
	const setDark = (dark: boolean): void => {
		root.classList.toggle("dark", dark)
	}
	setDark(computeDark())
	if (mode === "system") {
		const listener = (): void => {
			setDark(computeDark())
		}
		__cosShellThemeMediaListener = listener
		window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", listener)
	}
}

/** 壳内首跳 URL 带 `__cos_theme` 时首帧应用（与 WebView 注入互补）。 */
export function applyCosShellThemeFromUrl(): void {
	if (!isCosFlutterShell()) return
	const params = new URLSearchParams(window.location.search)
	const t = (params.get("__cos_theme") || "").trim().toLowerCase()
	if (t !== "light" && t !== "dark" && t !== "system") return
	applyCosShellThemeMode(t as CosShellThemeMode)
}

/** 独立浏览器打开 Portal：无壳时按系统深浅色切换 `html.dark`（非壳勿读 `__cos_theme`）。 */
export function applyBrowserDarkClassFromOsIfNotShell(): void {
	if (typeof document === "undefined") return
	if (isCosFlutterShell()) return
	const apply = (): void => {
		const dark = window.matchMedia("(prefers-color-scheme: dark)").matches
		document.documentElement.classList.toggle("dark", dark)
	}
	apply()
	window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", apply)
}

/** 壳首跳 `__cos_company`（Frappe Company.name），与原生 CosCompanyContext 一致。 */
export function cosShellCompanyFromUrl(): string | null {
	if (!isCosFlutterShell()) return null
	const params = new URLSearchParams(window.location.search)
	const c = (params.get("__cos_company") || "").trim()
	return c.length > 0 ? c : null
}

/** 写入 `data-cos-company` 与 `window.__COS_WORK_APP_COMPANY__`，供业务页筛选。 */
export function applyCosShellCompanyFromUrl(): void {
	if (typeof document === "undefined") return
	const name = cosShellCompanyFromUrl()
	if (!name) return
	document.documentElement.setAttribute("data-cos-company", name)
	;(window as unknown as { __COS_WORK_APP_COMPANY__?: string }).__COS_WORK_APP_COMPANY__ =
		name
}

import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"

declare global {
	interface Window {
		__WORKER_PORTAL_CONFIG__?: {
			apiBase?: string
			initialToken?: string | null
		}
	}
}

/** 与历史壳通过 URL fragment 注入 wpt 的约定一致（须先于 React 执行）。 */
const WPT_HASH_PREFIX = "#cosWorkerPortalToken="

function isCosWorkAppShell(): boolean {
	if (typeof navigator === "undefined") return false
	return /\bCosWorkApp\b/i.test(navigator.userAgent)
}

/** @returns 是否已从 hash 写入新的 wpt */
function applyWorkerPortalTokenFromHash(): boolean {
	if (typeof window === "undefined") return false
	const h = window.location.hash
	if (!h.startsWith(WPT_HASH_PREFIX)) return false
	try {
		const raw = h.slice(WPT_HASH_PREFIX.length)
		const token = decodeURIComponent(raw)
		if (token) localStorage.setItem("cos_worker_portal_token", token)
	} catch {
		/* ignore */
	}
	const clean = window.location.pathname + window.location.search
	window.history.replaceState(null, "", clean)
	return true
}

const wptInjectedFromHash = applyWorkerPortalTokenFromHash()
// 壳内已改为 Frappe Cookie 会话、不再经 hash 换发 wpt 时，localStorage 里往往残留旧 Bearer。
// POST 会优先带该 Bearer：非有效 wpt. 时既不豁免 CSRF 也不带 X-Frappe-CSRF-Token →「无效请求」；
// GET 列表仍正常，表现为仅详情打不开。
if (!wptInjectedFromHash && isCosWorkAppShell()) {
	try {
		localStorage.removeItem("cos_worker_portal_token")
	} catch {
		/* ignore */
	}
}

ReactDOM.createRoot(document.getElementById("worker-portal-root")!).render(
	<React.StrictMode>
		<App />
	</React.StrictMode>
)

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

/** 与 `cos_work_app` 中 `WorkerPortalTokenBootstrap` 的 fragment 约定一致（须先于 React 执行）。 */
const WPT_HASH_PREFIX = "#cosWorkerPortalToken="

function applyWorkerPortalTokenFromHash(): void {
	if (typeof window === "undefined") return
	const h = window.location.hash
	if (!h.startsWith(WPT_HASH_PREFIX)) return
	try {
		const raw = h.slice(WPT_HASH_PREFIX.length)
		const token = decodeURIComponent(raw)
		if (token) localStorage.setItem("cos_worker_portal_token", token)
	} catch {
		/* ignore */
	}
	const clean = window.location.pathname + window.location.search
	window.history.replaceState(null, "", clean)
}

applyWorkerPortalTokenFromHash()

ReactDOM.createRoot(document.getElementById("worker-portal-root")!).render(
	<React.StrictMode>
		<App />
	</React.StrictMode>
)

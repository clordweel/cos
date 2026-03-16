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

ReactDOM.createRoot(document.getElementById("worker-portal-root")!).render(
	<React.StrictMode>
		<App />
	</React.StrictMode>
)

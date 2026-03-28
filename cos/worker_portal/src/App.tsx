import { useEffect, useState } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from "react-router-dom"
import { Login } from "./pages/Login"
import { Stock } from "./pages/Stock"
import { PiReimbursementApproval } from "./pages/PiReimbursementApproval"
import {
	PiReimbursementPendingList,
	PiReimbursementPendingDetail,
} from "./pages/PiReimbursementPending"
import { getToken, getLoggedUser, clearToken } from "./lib/api"
import { isCosFlutterShell } from "./lib/clientEnv"
import { Button } from "./components/ui/button"
import { WpLoadingState, WpNotFoundState } from "./components/wp-states"
import { WpCentered, WpPage } from "./lib/wp-layout"
import { FlutterShellAuthRequired } from "./pages/FlutterShellAuthRequired"

const DEFAULT_LOGGED_IN_LANDING = "/worker-portal/pi-reimbursement-pending"

function loginPageState(fromPath: string): { from: string } {
	return { from: fromPath }
}

/** 受保护路由：未登录时去 Portal 自带登录页（勿整页跳 /login，否则仅有 Cookie、无 localStorage wpt 时会与 App 启动逻辑冲突形成死循环）。 */
function ProtectedRedirect() {
	const loc = useLocation()
	if (isCosFlutterShell()) {
		return <FlutterShellAuthRequired attemptedPath={loc.pathname + (loc.search || "")} />
	}
	const full = loc.pathname + (loc.search || "")
	return <Navigate to="/worker-portal/login" replace state={loginPageState(full)} />
}

function App() {
	const [user, setUser] = useState<string | null>(null)
	const [loginRedirectTo, setLoginRedirectTo] = useState<string | null>(null)
	const [loading, setLoading] = useState(true)

	useEffect(() => {
		let cancelled = false
		;(async () => {
			try {
				// 必须始终探测服务端会话：浏览器常仅有 Frappe Cookie、无 localStorage wpt；
				// 旧逻辑在 !token 时直接判未登录并跳 /login，会在「已 Desk 登录」场景下死循环。
				let u = await getLoggedUser()
				if (cancelled) return
				if ((!u || u === "Guest") && getToken()) {
					clearToken()
					u = await getLoggedUser()
					if (cancelled) return
				}
				setUser(u && u !== "Guest" ? u : null)
			} catch {
				clearToken()
				if (!cancelled) setUser(null)
			} finally {
				if (!cancelled) setLoading(false)
			}
		})()
		return () => {
			cancelled = true
		}
	}, [])

	const onLogin = (username: string, redirectTo?: string) => {
		setUser(username)
		setLoginRedirectTo(redirectTo || null)
	}

	if (loading) {
		return (
			<WpCentered>
				<WpLoadingState />
			</WpCentered>
		)
	}

	return (
		<BrowserRouter>
			<Routes>
				<Route
					path="/worker-portal/login"
					element={
						user ? (
							<Navigate
								to={loginRedirectTo || DEFAULT_LOGGED_IN_LANDING}
								replace
								state={null}
							/>
						) : (
							<Login onLogin={onLogin} />
						)
					}
				/>
				<Route path="/worker-portal/stock" element={user ? <Stock /> : <ProtectedRedirect />} />
				<Route
					path="/worker-portal/pi-reimbursement-pending/:piName"
					element={user ? <PiReimbursementPendingDetail /> : <ProtectedRedirect />}
				/>
				<Route
					path="/worker-portal/pi-reimbursement-pending"
					element={user ? <PiReimbursementPendingList /> : <ProtectedRedirect />}
				/>
				<Route path="/worker-portal/pi-reimbursement-approval" element={<PiReimbursementApproval />} />
				<Route
					path="/worker-portal"
					element={
						user ? (
							<Navigate to={DEFAULT_LOGGED_IN_LANDING} replace />
						) : (
							<ProtectedRedirect />
						)
					}
				/>
				<Route
					path="*"
					element={
						user ? (
							<WpPage>
								<WpNotFoundState
									title="页面不存在"
									description="地址可能已变更或输入有误。请强刷缓存后从下方入口进入。"
								>
									<Button asChild className="w-full">
										<Link to="/worker-portal/pi-reimbursement-pending">待报销采购发票</Link>
									</Button>
									<Button variant="outline" asChild className="w-full">
										<Link to="/worker-portal/stock">入库盘点</Link>
									</Button>
								</WpNotFoundState>
							</WpPage>
						) : (
							<ProtectedRedirect />
						)
					}
				/>
			</Routes>
		</BrowserRouter>
	)
}

export default App

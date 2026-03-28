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

function ProtectedRedirect() {
	const loc = useLocation()
	if (isCosFlutterShell()) {
		return <FlutterShellAuthRequired attemptedPath={loc.pathname + (loc.search || "")} />
	}
	// 浏览器：勿跳 Frappe `/login`。该登录只写 Cookie，不会写入 Portal 所需的
	// `localStorage.cos_worker_portal_token`（wpt），回到 SPA 后仍无 token → 无限重定向。
	// 必须走 `/worker-portal/login`（login_for_token）与壳一致。
	const from = (loc.pathname + (loc.search || "")).trim() || DEFAULT_LOGGED_IN_LANDING
	return <Navigate to="/worker-portal/login" replace state={{ from }} />
}

function App() {
	const [user, setUser] = useState<string | null>(null)
	const [loginRedirectTo, setLoginRedirectTo] = useState<string | null>(null)
	const [loading, setLoading] = useState(true)

	useEffect(() => {
		const token = getToken()
		if (!token) {
			setUser(null)
			setLoading(false)
			return
		}
		getLoggedUser()
			.then((u) => {
				setUser(u && u !== "Guest" ? u : null)
			})
			.catch(() => {
				clearToken()
				setUser(null)
			})
			.finally(() => setLoading(false))
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

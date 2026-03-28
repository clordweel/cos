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
import { WpAuthPage, WpCentered, WpPage } from "./lib/wp-layout"
import { FlutterShellAuthRequired } from "./pages/FlutterShellAuthRequired"

const DEFAULT_LOGGED_IN_LANDING = "/worker-portal/pi-reimbursement-pending"

function ProtectedRedirect() {
	const loc = useLocation()
	if (isCosFlutterShell()) {
		return <FlutterShellAuthRequired attemptedPath={loc.pathname + (loc.search || "")} />
	}
	const full = loc.pathname + (loc.search || "")
	const q = encodeURIComponent(full)
	window.location.replace(`/login?redirect-to=${q}`)
	return (
		<WpAuthPage>
			<WpLoadingState label="正在跳转系统登录…" />
		</WpAuthPage>
	)
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

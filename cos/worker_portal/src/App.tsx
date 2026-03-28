import { useEffect, useState } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import { Login } from "./pages/Login"
import { Stock } from "./pages/Stock"
import { PiReimbursementApproval } from "./pages/PiReimbursementApproval"
import {
	PiReimbursementPendingList,
	PiReimbursementPendingDetail,
} from "./pages/PiReimbursementPending"
import { getToken, getLoggedUser, clearToken } from "./lib/api"
import { isCosFlutterShell } from "./lib/clientEnv"
import { WpCentered, WpPage, wpText } from "./lib/wp-layout"
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
		<WpCentered>
			<p className={wpText.muted}>正在跳转系统登录…</p>
		</WpCentered>
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
				<div className="animate-pulse text-muted-foreground text-sm">加载中...</div>
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
								<p className={`${wpText.muted} text-center`}>
									路径未识别，请强刷后重试。
								</p>
								<div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
									<a
										className="text-sm font-medium text-primary underline underline-offset-4 text-center"
										href="/worker-portal/pi-reimbursement-pending"
									>
										待报销审批
									</a>
									<a
										className="text-sm text-muted-foreground underline underline-offset-4 text-center"
										href="/worker-portal/stock"
									>
										入库盘点
									</a>
								</div>
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

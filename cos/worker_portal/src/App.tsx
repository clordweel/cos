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
		<div className="min-h-screen flex items-center justify-center">
			<p className="text-muted-foreground text-sm">正在跳转系统登录…</p>
		</div>
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
			<div className="min-h-screen flex items-center justify-center">
				<div className="animate-pulse text-muted-foreground">加载中...</div>
			</div>
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
							<div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 text-center text-sm">
								<p className="text-muted-foreground max-w-md">
									当前页面路径未识别（可能是浏览器仍在使用旧版 Worker Portal 脚本）。
									请<strong>强刷</strong>或清除站点数据后重试；完整地址应为{" "}
									<code className="text-xs break-all">/worker-portal/pi-reimbursement-pending</code>。
								</p>
								<a className="text-primary underline" href="/worker-portal/pi-reimbursement-pending">
									打开待报销审批
								</a>
								<a className="text-muted-foreground underline text-xs" href="/worker-portal/stock">
									打开入库盘点
								</a>
							</div>
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

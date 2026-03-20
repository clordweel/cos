import { useEffect, useState } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import { Workbench } from "./pages/Workbench"
import { Login } from "./pages/Login"
import { Approval } from "./pages/Approval"
import { ApprovalDetail } from "./pages/ApprovalDetail"
import { Stock } from "./pages/Stock"
import { PiReimbursementApproval } from "./pages/PiReimbursementApproval"
import {
	PiReimbursementPendingList,
	PiReimbursementPendingDetail,
} from "./pages/PiReimbursementPending"
import { getToken, getLoggedUser, clearToken } from "./lib/api"

function ProtectedRedirect() {
	const loc = useLocation()
	return <Navigate to="/worker-portal/login" replace state={{ from: loc.pathname }} />
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

	const onLogout = () => {
		clearToken()
		setUser(null)
		setLoginRedirectTo(null)
	}

	if (loading) {
		return (
			<div className="min-h-screen flex items-center justify-center">
				<div className="animate-pulse text-muted-foreground">加载中...</div>
			</div>
		)
	}

	// 注意：更长的 /worker-portal/... 必须写在精确路径 /worker-portal 之前，避免部分环境下误匹配。
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/worker-portal/login" element={user ? <Navigate to={loginRedirectTo || "/worker-portal"} replace state={null} /> : <Login onLogin={onLogin} />} />
				<Route path="/worker-portal/approval/:id" element={user ? <ApprovalDetail /> : <ProtectedRedirect />} />
				<Route path="/worker-portal/approval" element={user ? <Approval /> : <ProtectedRedirect />} />
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
				<Route path="/worker-portal" element={user ? <Workbench user={user} onLogout={onLogout} /> : <ProtectedRedirect />} />
				{/* 未注册路径：勿静默回工作台（易掩盖旧 JS 无新路由）；已登录时提示并给出待批入口 */}
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
								<a className="text-muted-foreground underline text-xs" href="/worker-portal">
									回工作台
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

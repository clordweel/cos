import { useEffect, useState } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import { Workbench } from "./pages/Workbench"
import { Login } from "./pages/Login"
import { Approval } from "./pages/Approval"
import { ApprovalDetail } from "./pages/ApprovalDetail"
import { Stock } from "./pages/Stock"
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

	return (
		<BrowserRouter>
			<Routes>
				<Route path="/worker-portal/login" element={user ? <Navigate to={loginRedirectTo || "/worker-portal"} replace state={null} /> : <Login onLogin={onLogin} />} />
				<Route path="/worker-portal" element={user ? <Workbench user={user} onLogout={onLogout} /> : <ProtectedRedirect />} />
				<Route path="/worker-portal/approval" element={user ? <Approval /> : <ProtectedRedirect />} />
				<Route path="/worker-portal/approval/:id" element={user ? <ApprovalDetail /> : <ProtectedRedirect />} />
				<Route path="/worker-portal/stock" element={user ? <Stock /> : <ProtectedRedirect />} />
				<Route path="*" element={<Navigate to={user ? "/worker-portal" : "/worker-portal/login"} replace />} />
			</Routes>
		</BrowserRouter>
	)
}

export default App

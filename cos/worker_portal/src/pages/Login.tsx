import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { login, setToken } from "@/lib/api"
import { WpAuthPage, wpText } from "@/lib/wp-layout"

interface LoginProps {
	onLogin: (user: string, redirectTo?: string) => void
}

export function Login({ onLogin }: LoginProps) {
	const location = useLocation()
	const navigate = useNavigate()
	const from = (location.state as { from?: string })?.from || "/worker-portal/pi-reimbursement-pending"
	const [username, setUsername] = useState("")
	const [password, setPassword] = useState("")
	const [error, setError] = useState("")
	const [loading, setLoading] = useState(false)

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault()
		setError("")
		setLoading(true)
		try {
			const res = await login(username, password)
			setToken(res.token)
			onLogin(res.user, from)
			navigate(from, { replace: true })
		} catch (err) {
			setError(err instanceof Error ? err.message : "登录失败")
		} finally {
			setLoading(false)
		}
	}

	return (
		<WpAuthPage>
			<Card className="w-full">
				<CardHeader>
					<CardTitle>登录</CardTitle>
				</CardHeader>
				<CardContent>
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="space-y-2">
							<Label htmlFor="usr">账号</Label>
							<Input
								id="usr"
								type="text"
								value={username}
								onChange={(e) => setUsername(e.target.value)}
								required
								autoComplete="username"
							/>
						</div>
						<div className="space-y-2">
							<Label htmlFor="pwd">密码</Label>
							<Input
								id="pwd"
								type="password"
								value={password}
								onChange={(e) => setPassword(e.target.value)}
								required
								autoComplete="current-password"
							/>
						</div>
						{error && <p className={wpText.error}>{error}</p>}
						<Button type="submit" className="w-full" disabled={loading}>
							{loading ? "登录中..." : "登录"}
						</Button>
					</form>
				</CardContent>
			</Card>
		</WpAuthPage>
	)
}

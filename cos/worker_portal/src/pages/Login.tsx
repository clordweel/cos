import { useState } from "react"
import { useLocation } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { login, setToken } from "@/lib/api"

interface LoginProps {
	onLogin: (user: string) => void
}

export function Login({ onLogin }: LoginProps) {
	const location = useLocation()
	const from = (location.state as { from?: string })?.from || "/worker-portal"
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
		} catch (err) {
			setError(err instanceof Error ? err.message : "登录失败")
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="min-h-screen flex items-center justify-center p-4 bg-muted/30">
			<Card className="w-full max-w-md">
				<CardHeader>
					<CardTitle>登录</CardTitle>
					<CardDescription>登录成功后将跳转到工作台</CardDescription>
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
						{error && (
							<p className="text-sm text-destructive">{error}</p>
						)}
						<Button type="submit" className="w-full" disabled={loading}>
							{loading ? "登录中..." : "登录"}
						</Button>
					</form>
				</CardContent>
			</Card>
		</div>
	)
}

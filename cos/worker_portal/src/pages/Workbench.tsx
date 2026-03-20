import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ClipboardList, Package, LogOut, FileCheck } from "lucide-react"
import { clearToken } from "@/lib/api"

interface WorkbenchProps {
	user: string
	onLogout: () => void
}

const modules = [
	{
		title: "待报销审批",
		description: "登录后审批待处理的员工垫付采购发票（不依赖邮件链接）",
		href: "/worker-portal/pi-reimbursement-pending",
		icon: FileCheck,
	},
	{
		title: "垫付 · 已批待 JE",
		description:
			"仅含报销审批已通过、尚未报销的采购发票，用于创建应付转员工 JE（不是待审批列表）",
		href: "/worker-portal/approval",
		icon: ClipboardList,
	},
	{
		title: "入库盘点",
		description: "库存盘点与调整",
		href: "/worker-portal/stock",
		icon: Package,
	},
]

export function Workbench({ user, onLogout }: WorkbenchProps) {
	function handleLogout() {
		clearToken()
		onLogout()
	}

	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3 flex items-center justify-between">
				<h1 className="text-xl font-semibold">工作台</h1>
				<div className="flex items-center gap-2">
					<span className="text-sm text-muted-foreground">{user}</span>
					<Button variant="ghost" size="sm" onClick={handleLogout}>
						<LogOut className="h-4 w-4 mr-1" />
						退出
					</Button>
				</div>
			</header>
			<main className="container max-w-2xl py-8 px-4">
				<div className="space-y-4">
					{modules.map((m) => {
						const Icon = m.icon
						return (
							<Link
								key={m.href}
								to={m.href}
								className="block"
							>
								<Card className="hover:bg-accent/50 transition-colors cursor-pointer">
									<CardHeader className="flex flex-row items-center gap-4">
										<div className="rounded-lg bg-primary/10 p-3">
											<Icon className="h-6 w-6 text-primary" />
										</div>
										<div className="flex-1">
											<CardTitle className="text-lg">{m.title}</CardTitle>
											<CardDescription>{m.description}</CardDescription>
										</div>
									</CardHeader>
								</Card>
							</Link>
						)
					})}
				</div>
			</main>
		</div>
	)
}

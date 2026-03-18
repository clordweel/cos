import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Loader2 } from "lucide-react"
import { listEmployeeAdvancePending, type EmployeeAdvanceItem } from "@/lib/api"

function formatCurrency(n: number): string {
	return new Intl.NumberFormat("zh-CN", {
		style: "currency",
		currency: "CNY",
	}).format(n)
}

function formatDate(s: string | null): string {
	if (!s) return "-"
	try {
		return new Date(s).toLocaleDateString("zh-CN")
	} catch {
		return s
	}
}

export function Approval() {
	const navigate = useNavigate()
	const [items, setItems] = useState<EmployeeAdvanceItem[]>([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		listEmployeeAdvancePending()
			.then(setItems)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [])

	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3">
				<Link
					to="/worker-portal"
					className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
				>
					<ArrowLeft className="h-4 w-4 mr-2" />
					返回工作台
				</Link>
			</header>
			<main className="container max-w-md py-4 px-3 sm:px-4">
				<div className="space-y-4">
					<div>
						<h1 className="text-lg font-semibold">采购垫付报销审批</h1>
						<p className="text-sm text-muted-foreground mt-0.5">
							点击卡片查看详情并创建应付转员工 JE
						</p>
					</div>
					{loading && (
						<div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
							<Loader2 className="h-6 w-6 animate-spin mr-2" />
							加载中...
						</div>
					)}
					{error && (
						<div className="py-6 text-center text-destructive text-sm">{error}</div>
					)}
					{!loading && !error && items.length === 0 && (
						<div className="py-12 text-center text-muted-foreground text-sm rounded-lg border border-dashed bg-background">
							暂无待审批记录
						</div>
					)}
					{!loading && !error && items.length > 0 && (
						<ul className="space-y-3">
							{items.map((row) => (
								<li key={row.name}>
									<Card className="overflow-hidden">
										<CardContent className="p-4 pb-3">
											{/* 标题：强调金额 */}
											<div className="flex items-start justify-between gap-2 mb-1">
												<span className="text-xl font-semibold tracking-tight">
													{formatCurrency(row.grand_total ?? 0)}
												</span>
												{row.custom_payable_transfer_je ? (
													<Badge variant="success" className="text-[10px] px-2 py-0.5 shrink-0">
														已创建
													</Badge>
												) : (
													<Badge variant="warning" className="text-[10px] px-2 py-0.5 shrink-0">
														待创建
													</Badge>
												)}
											</div>
											{/* 弱化：单据号 */}
											<p className="text-xs text-muted-foreground mb-2">
												{row.name}
											</p>
											{/* 正文：员工、日期 */}
											<p className="text-sm text-foreground/90">
												{row.custom_advance_employee || "未知员工"} · {formatDate(row.posting_date)}
											</p>
										</CardContent>
										{/* 底部操作 */}
										<div className="border-t px-4 py-2.5 bg-muted/30">
											<Button
												variant="outline"
												size="sm"
												className="w-full"
												onClick={() => navigate(`/worker-portal/approval/${row.name}`)}
											>
												查看详情
											</Button>
										</div>
									</Card>
								</li>
							))}
						</ul>
					)}
				</div>
			</main>
		</div>
	)
}

import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, ChevronRight, Loader2 } from "lucide-react"
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
									<Card
										className="cursor-pointer transition-colors hover:bg-accent/50 active:bg-accent"
										onClick={() => navigate(`/worker-portal/approval/${row.name}`)}
									>
										<CardContent className="p-4">
											<div className="flex items-start justify-between gap-3">
												<div className="min-w-0 flex-1 space-y-1">
													<p className="font-medium text-sm truncate">
														{row.custom_advance_employee || "未知员工"}
													</p>
													<div className="flex items-center gap-2 text-xs text-muted-foreground">
														<span className="font-medium text-foreground">
															{formatCurrency(row.grand_total ?? 0)}
														</span>
														<span>·</span>
														<span>{formatDate(row.posting_date)}</span>
													</div>
												</div>
												<div className="flex shrink-0 items-center gap-2">
													{row.custom_payable_transfer_je ? (
														<Badge variant="success" className="text-[10px] px-2 py-0.5">
															已创建
														</Badge>
													) : (
														<Badge variant="warning" className="text-[10px] px-2 py-0.5">
															待创建
														</Badge>
													)}
													<ChevronRight className="h-4 w-4 text-muted-foreground" />
												</div>
											</div>
										</CardContent>
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

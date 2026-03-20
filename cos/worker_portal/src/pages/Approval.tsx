import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import dayjs from "dayjs"
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
	const d = dayjs(s)
	return d.isValid() ? d.format("YYYY/M/D") : s
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
			<header className="border-b bg-background px-4 py-4 sm:px-6">
				<Link
					to="/worker-portal"
					className="inline-flex items-center gap-2 rounded-md px-1 py-1.5 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground -ml-1"
				>
					<ArrowLeft className="h-4 w-4 shrink-0" />
					返回工作台
				</Link>
			</header>
			<main className="w-full max-w-md mx-auto px-6 py-6 sm:px-8 sm:py-8">
				<div className="space-y-6">
					<div className="space-y-1.5">
						<h1 className="text-lg font-semibold leading-tight tracking-tight">
							垫付 · 应付转员工 JE
						</h1>
						<p className="text-sm text-muted-foreground leading-relaxed">
							仅展示<strong>报销审批已通过</strong>且<strong>尚未报销</strong>的采购发票，用于创建应付转员工 JE。
							待批/外链审批请使用 Desk「生成报销审批链接」，不在本页。
						</p>
					</div>
					{loading && (
						<div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
							<Loader2 className="h-6 w-6 animate-spin mr-2" />
							加载中...
						</div>
					)}
					{error && (
						<div className="py-12 text-center text-destructive text-sm">{error}</div>
					)}
					{!loading && !error && items.length === 0 && (
						<div className="py-16 px-6 text-center text-muted-foreground text-sm rounded-lg border border-dashed bg-background space-y-2">
							<p>暂无待处理记录</p>
							<p className="text-xs">
								当前列表仅展示「报销已通过并已提交」的垫付发票。若仍无数据，请先在 Desk 完成发票上的报销审批并提交采购发票。
							</p>
						</div>
					)}
					{!loading && !error && items.length > 0 && (
						<ul className="space-y-4">
							{items.map((row) => (
								<li key={row.name}>
									<Card className="overflow-hidden">
										<CardContent className="p-6 space-y-3">
											{/* 首行：单据号左上角最小字，报销状态右上角 */}
											<div className="flex items-start justify-between gap-2">
												<span className="text-[10px] text-muted-foreground leading-none">
													{row.name}
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
											{/* 金额 */}
											<span className="text-xl font-semibold tracking-tight leading-tight block">
												{formatCurrency(row.grand_total ?? 0)}
											</span>
											{/* 员工姓名、日期 */}
											<p className="text-sm text-foreground/90 leading-relaxed">
												{row.employee_name || row.custom_advance_employee || "未知员工"} · {formatDate(row.posting_date)}
											</p>
										</CardContent>
										{/* 底部操作：shadcn CardFooter 风格 */}
										<div className="border-t px-6 py-4 bg-muted/30">
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

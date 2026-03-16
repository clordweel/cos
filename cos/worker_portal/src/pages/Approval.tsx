import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table"
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
			<main className="container max-w-4xl py-4 px-3 sm:px-4">
				<Card>
					<CardHeader className="p-4 pb-2">
						<CardTitle className="text-lg">采购垫付报销审批</CardTitle>
						<CardDescription className="text-xs mt-0.5">
							员工垫付未报销的采购发票，点击行查看详情并创建应付转员工 JE
						</CardDescription>
					</CardHeader>
					<CardContent className="p-4 pt-0">
						{loading && (
							<div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
								<Loader2 className="h-6 w-6 animate-spin mr-2" />
								加载中...
							</div>
						)}
						{error && (
							<div className="py-6 text-center text-destructive text-sm">{error}</div>
						)}
						{!loading && !error && items.length === 0 && (
							<div className="py-8 text-center text-muted-foreground text-sm">
								暂无待审批记录
							</div>
						)}
						{!loading && !error && items.length > 0 && (
							<Table className="min-w-[32rem]">
								<TableHeader>
									<TableRow>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium">单据号</TableHead>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium">供应商</TableHead>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium">垫付员工</TableHead>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium text-right">金额</TableHead>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium">过账日期</TableHead>
										<TableHead className="h-9 px-2 py-2 text-xs font-medium">JE 状态</TableHead>
										<TableHead className="h-9 w-8 px-1" />
									</TableRow>
								</TableHeader>
								<TableBody>
									{items.map((row) => (
										<TableRow
											key={row.name}
											className="cursor-pointer"
											onClick={() => navigate(`/worker-portal/approval/${row.name}`)}
										>
											<TableCell className="px-2 py-2 text-xs font-medium whitespace-nowrap">{row.name}</TableCell>
											<TableCell className="px-2 py-2 text-xs whitespace-nowrap">{row.supplier || "-"}</TableCell>
											<TableCell className="px-2 py-2 text-xs whitespace-nowrap">{row.custom_advance_employee || "-"}</TableCell>
											<TableCell className="px-2 py-2 text-xs text-right whitespace-nowrap">
												{formatCurrency(row.grand_total ?? 0)}
											</TableCell>
											<TableCell className="px-2 py-2 text-xs whitespace-nowrap">
												{formatDate(row.posting_date)}
											</TableCell>
											<TableCell className="px-2 py-2">
												{row.custom_payable_transfer_je ? (
													<Badge variant="success" className="text-[10px] px-1.5 py-0">已创建</Badge>
												) : (
													<Badge variant="warning" className="text-[10px] px-1.5 py-0">待创建</Badge>
												)}
											</TableCell>
											<TableCell className="px-1 py-2">
												<ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
											</TableCell>
										</TableRow>
									))}
								</TableBody>
							</Table>
						)}
					</CardContent>
				</Card>
			</main>
		</div>
	)
}

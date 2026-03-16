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
			<main className="container max-w-4xl py-8 px-4">
				<Card>
					<CardHeader>
						<CardTitle>采购垫付报销审批</CardTitle>
						<CardDescription>
							员工垫付未报销的采购发票列表，点击行可查看详情并创建应付转员工日记账
						</CardDescription>
					</CardHeader>
					<CardContent>
						{loading && (
							<div className="flex items-center justify-center py-12 text-muted-foreground">
								<Loader2 className="h-8 w-8 animate-spin mr-2" />
								加载中...
							</div>
						)}
						{error && (
							<div className="py-8 text-center text-destructive">{error}</div>
						)}
						{!loading && !error && items.length === 0 && (
							<div className="py-12 text-center text-muted-foreground">
								暂无待审批记录
							</div>
						)}
						{!loading && !error && items.length > 0 && (
							<Table>
								<TableHeader>
									<TableRow>
										<TableHead>单据号</TableHead>
										<TableHead>供应商</TableHead>
										<TableHead>垫付员工</TableHead>
										<TableHead className="text-right">金额</TableHead>
										<TableHead>过账日期</TableHead>
										<TableHead>JE 状态</TableHead>
										<TableHead className="w-10" />
									</TableRow>
								</TableHeader>
								<TableBody>
									{items.map((row) => (
										<TableRow
											key={row.name}
											className="cursor-pointer"
											onClick={() => navigate(`/worker-portal/approval/${row.name}`)}
										>
											<TableCell className="font-medium">{row.name}</TableCell>
											<TableCell>{row.supplier || "-"}</TableCell>
											<TableCell>{row.custom_advance_employee || "-"}</TableCell>
											<TableCell className="text-right">
												{formatCurrency(row.grand_total ?? 0)}
											</TableCell>
											<TableCell>{formatDate(row.posting_date)}</TableCell>
											<TableCell>
												{row.custom_payable_transfer_je ? (
													<Badge variant="success">已创建 JE</Badge>
												) : (
													<Badge variant="warning">待创建</Badge>
												)}
											</TableCell>
											<TableCell>
												<ChevronRight className="h-4 w-4 text-muted-foreground" />
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

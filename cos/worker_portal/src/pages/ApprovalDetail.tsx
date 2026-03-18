import { useEffect, useState } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import dayjs from "dayjs"
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
import { ArrowLeft, Loader2, FileText } from "lucide-react"
import {
	getPurchaseInvoiceDetail,
	createPayableTransferJe,
	type PurchaseInvoiceDetail,
} from "@/lib/api"

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

export function ApprovalDetail() {
	const { id } = useParams<{ id: string }>()
	const navigate = useNavigate()
	const [detail, setDetail] = useState<PurchaseInvoiceDetail | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [creating, setCreating] = useState(false)

	useEffect(() => {
		if (!id) {
			setLoading(false)
			return
		}
		getPurchaseInvoiceDetail(id)
			.then(setDetail)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [id])

	const handleCreateJe = async () => {
		if (!id || !detail) return
		setCreating(true)
		setError(null)
		try {
			await createPayableTransferJe(id)
			// 刷新详情
			const d = await getPurchaseInvoiceDetail(id)
			setDetail(d)
		} catch (e) {
			setError((e as Error)?.message ?? "创建失败")
		} finally {
			setCreating(false)
		}
	}

	if (!id) {
		return (
			<div className="min-h-screen bg-muted/30 flex items-center justify-center">
				<div className="text-muted-foreground">缺少单据号</div>
				<Link to="/worker-portal/approval">
					<Button variant="outline" className="ml-4">
						返回列表
					</Button>
				</Link>
			</div>
		)
	}

	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3">
				<Link
					to="/worker-portal/approval"
					className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
				>
					<ArrowLeft className="h-4 w-4 mr-2" />
					返回审批列表
				</Link>
			</header>
			<main className="container max-w-3xl py-8 px-4">
				{loading && (
					<div className="flex items-center justify-center py-12 text-muted-foreground">
						<Loader2 className="h-8 w-8 animate-spin mr-2" />
						加载中...
					</div>
				)}
				{error && (
					<Card className="mb-6">
						<CardContent className="pt-6">
							<div className="text-destructive mb-4">{error}</div>
							<Button variant="outline" onClick={() => navigate("/worker-portal/approval")}>
								返回列表
							</Button>
						</CardContent>
					</Card>
				)}
				{!loading && detail && (
					<>
						<Card className="mb-6">
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<div>
									<CardTitle className="flex items-center gap-2">
										<FileText className="h-5 w-5" />
										{detail.name}
									</CardTitle>
									<CardDescription>
										采购发票 · 过账日期 {formatDate(detail.posting_date)}
									</CardDescription>
								</div>
								<Badge
									variant={detail.custom_payable_transfer_je ? "success" : "warning"}
								>
									{detail.custom_payable_transfer_je ? "已创建 JE" : "待创建 JE"}
								</Badge>
							</CardHeader>
							<CardContent className="space-y-4">
								<div className="grid grid-cols-2 gap-4 text-sm">
									<div>
										<span className="text-muted-foreground">供应商：</span>
										{detail.supplier || "-"}
									</div>
									<div>
										<span className="text-muted-foreground">垫付员工：</span>
										{detail.employee_name || detail.custom_advance_employee || "-"}
									</div>
									<div>
										<span className="text-muted-foreground">报销状态：</span>
										{detail.custom_employee_reimbursed || "未报销"}
									</div>
									<div>
										<span className="text-muted-foreground">总金额：</span>
										<span className="font-medium">
											{formatCurrency(detail.grand_total ?? 0)}
										</span>
									</div>
									{detail.custom_payable_transfer_je && (
										<div className="col-span-2">
											<span className="text-muted-foreground">应付转员工 JE：</span>
											{detail.custom_payable_transfer_je}
										</div>
									)}
								</div>
								{!detail.custom_payable_transfer_je && (
									<Button
										onClick={handleCreateJe}
										disabled={creating}
										className="w-full sm:w-auto"
									>
										{creating ? (
											<>
												<Loader2 className="h-4 w-4 mr-2 animate-spin" />
												创建中...
											</>
										) : (
											"创建应付转员工日记账"
										)}
									</Button>
								)}
							</CardContent>
						</Card>
						<Card>
							<CardHeader>
								<CardTitle>物料明细</CardTitle>
								<CardDescription>采购发票行项目</CardDescription>
							</CardHeader>
							<CardContent>
								<Table>
									<TableHeader>
										<TableRow>
											<TableHead>物料编码</TableHead>
											<TableHead>物料名称</TableHead>
											<TableHead className="text-right">数量</TableHead>
											<TableHead className="text-right">单价</TableHead>
											<TableHead className="text-right">金额</TableHead>
										</TableRow>
									</TableHeader>
									<TableBody>
										{(detail.items ?? []).map((row, i) => (
											<TableRow key={i}>
												<TableCell className="font-medium">
													{row.item_code || "-"}
												</TableCell>
												<TableCell>{row.item_name || "-"}</TableCell>
												<TableCell className="text-right">{row.qty}</TableCell>
												<TableCell className="text-right">
													{formatCurrency(row.rate ?? 0)}
												</TableCell>
												<TableCell className="text-right">
													{formatCurrency(row.amount ?? 0)}
												</TableCell>
											</TableRow>
										))}
									</TableBody>
								</Table>
								{(detail.items ?? []).length === 0 && (
									<div className="py-8 text-center text-muted-foreground">
										无物料明细
									</div>
								)}
							</CardContent>
						</Card>
					</>
				)}
			</main>
		</div>
	)
}

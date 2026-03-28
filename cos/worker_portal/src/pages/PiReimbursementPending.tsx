import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft } from "lucide-react"
import {
	listPiReimbursementPendingApproval,
	getPiSummaryForLoggedInApproval,
	approvePiLoggedIn,
	type PiReimbursementSummary,
	type PiReimbursementPendingRow,
} from "@/lib/api"

function formatCurrency(n: number): string {
	return new Intl.NumberFormat("zh-CN", {
		style: "currency",
		currency: "CNY",
	}).format(n)
}

/** 待审批列表（需登录） */
export function PiReimbursementPendingList() {
	const [rows, setRows] = useState<PiReimbursementPendingRow[]>([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		listPiReimbursementPendingApproval(100)
			.then(setRows)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [])

	if (loading) {
		return (
			<div className="flex min-h-[40vh] items-center justify-center">
				<p className="text-muted-foreground">加载中...</p>
			</div>
		)
	}

	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3">
				<div className="container max-w-2xl flex items-center gap-3">
					<h1 className="text-lg font-semibold">待报销审批</h1>
				</div>
			</header>
			<main className="container max-w-2xl py-6 px-4 space-y-3">
				<details className="rounded-lg border bg-background px-4 py-3 text-sm open:pb-4">
					<summary className="cursor-pointer font-medium text-foreground">
						如何产生「待报销审批」列表中的记录？
					</summary>
					<ol className="mt-3 list-decimal pl-5 space-y-2 text-muted-foreground leading-relaxed">
						<li>
							在 Desk 打开 <strong className="text-foreground">采购发票 (Purchase Invoice)</strong>
							，填好供应商、明细、金额等常规字段。
						</li>
						<li>
							勾选 <strong className="text-foreground">员工垫付</strong>（<code className="text-xs">custom_is_employee_advance</code>
							），并选择 <strong className="text-foreground">垫付员工</strong>。
						</li>
						<li>
							<strong className="text-foreground">报销审批状态</strong>须为{" "}
							<strong className="text-foreground">Pending</strong> 或留空；已 Approved / Rejected
							不会出现在本列表。
						</li>
						<li>
							<strong className="text-foreground">必须「提交」采购发票</strong>（已记账的 Submitted
							状态）。仅保存为草稿的单据<strong>不会</strong>出现在本列表。
						</li>
						<li>
							从带员工垫付的 <strong className="text-foreground">采购订单</strong>下推 PI
							时，通常会自动带出垫付勾选与员工，仍需确认上述字段并提交 PI。
						</li>
						<li>
							当前登录用户在 Frappe 中须对这张 PI 有 <strong className="text-foreground">读权限</strong>
							（列表才会显示）；点进详情批准/拒绝需要{" "}
							<strong className="text-foreground">写权限</strong>。
						</li>
					</ol>
					<p className="mt-3 text-xs text-muted-foreground border-t pt-3">
						说明：创建「应付转员工 JE」仍要求报销审批为 Approved；未通过前系统会拦截 JE/付给员工，与是否已提交
						PI 无关。
					</p>
				</details>
				{error && <p className="text-sm text-destructive">{error}</p>}
				{!error && rows.length === 0 && (
					<div className="rounded-lg border border-dashed bg-muted/30 px-4 py-6 text-sm text-muted-foreground space-y-2">
						<p className="font-medium text-foreground">暂无待审批的采购发票</p>
						<p>
							请展开上方说明，在 Desk 按步骤准备一张<strong>已提交</strong>、<strong>员工垫付</strong>、
							<strong>审批仍为 Pending</strong> 的 PI。若仍为空，请到列表筛选里用「报销审批状态 = Pending」在
							PI 列表中自查是否存在符合条件但当前账号无读权限的单据。
						</p>
					</div>
				)}
				{rows.map((r) => (
					<Link
						key={r.name}
						to={`/worker-portal/pi-reimbursement-pending/${encodeURIComponent(r.name)}`}
						className="block"
					>
						<Card className="hover:bg-accent/50 transition-colors">
							<CardHeader className="py-3">
								<CardTitle className="text-base">{r.name}</CardTitle>
								<p className="text-sm text-muted-foreground">
									{r.supplier || "-"} · 过账 {r.posting_date || "-"}
								</p>
							</CardHeader>
							<CardContent className="pt-0 pb-3 text-sm">
								<div className="flex justify-between">
									<span className="text-muted-foreground">垫付员工</span>
									<span>{r.employee_name || r.custom_advance_employee || "-"}</span>
								</div>
								<div className="flex justify-between mt-1">
									<span className="text-muted-foreground">金额</span>
									<span className="font-medium">{formatCurrency(r.grand_total ?? 0)}</span>
								</div>
							</CardContent>
						</Card>
					</Link>
				))}
			</main>
		</div>
	)
}

/** 单张 PI 审批（需登录 + 写权限） */
export function PiReimbursementPendingDetail() {
	const { piName: raw } = useParams<{ piName: string }>()
	const piName = raw ? decodeURIComponent(raw) : ""
	const [summary, setSummary] = useState<PiReimbursementSummary | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [result, setResult] = useState<"approved" | "rejected" | null>(null)
	const [submitting, setSubmitting] = useState(false)
	const [rejectRemark, setRejectRemark] = useState("")
	const [showRejectInput, setShowRejectInput] = useState(false)

	useEffect(() => {
		if (!piName) {
			setLoading(false)
			setError("缺少采购发票编号")
			return
		}
		getPiSummaryForLoggedInApproval(piName)
			.then(setSummary)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [piName])

	const handleApprove = async () => {
		if (!piName || !summary) return
		setSubmitting(true)
		setError(null)
		try {
			await approvePiLoggedIn(piName, "approve", "")
			setResult("approved")
		} catch (e) {
			setError((e as Error)?.message ?? "审批失败")
		} finally {
			setSubmitting(false)
		}
	}

	const handleReject = async () => {
		if (!piName || !summary) return
		if (!showRejectInput) {
			setShowRejectInput(true)
			return
		}
		setSubmitting(true)
		setError(null)
		try {
			await approvePiLoggedIn(piName, "reject", rejectRemark)
			setResult("rejected")
		} catch (e) {
			setError((e as Error)?.message ?? "审批失败")
		} finally {
			setSubmitting(false)
		}
	}

	if (loading) {
		return (
			<div className="flex min-h-[40vh] items-center justify-center">
				<p className="text-muted-foreground">加载中...</p>
			</div>
		)
	}

	if (error && !summary) {
		return (
			<div className="mx-auto max-w-md space-y-4 p-6">
				<Button variant="ghost" size="sm" asChild className="mb-2">
					<Link to="/worker-portal/pi-reimbursement-pending">
						<ArrowLeft className="h-4 w-4 mr-1" />
						返回列表
					</Link>
				</Button>
				<Card>
					<CardContent className="pt-6">
						<p className="text-destructive">{error}</p>
						<p className="mt-2 text-sm text-muted-foreground">
							若无读权限或单据已审批，将无法打开。
						</p>
					</CardContent>
				</Card>
			</div>
		)
	}

	if (result) {
		return (
			<div className="mx-auto max-w-md space-y-4 p-6">
				<Card>
					<CardContent className="pt-6 space-y-4">
						<p className="text-lg font-medium">
							{result === "approved" ? "已批准" : "已拒绝"}
						</p>
						<Button asChild className="w-full">
							<Link to="/worker-portal/pi-reimbursement-pending">返回待审批列表</Link>
						</Button>
					</CardContent>
				</Card>
			</div>
		)
	}

	if (!summary) return null

	return (
		<div className="min-h-screen bg-muted/30">
			<header className="border-b bg-background px-4 py-3">
				<div className="container max-w-md flex items-center gap-2">
					<Button variant="ghost" size="sm" asChild>
						<Link to="/worker-portal/pi-reimbursement-pending">
							<ArrowLeft className="h-4 w-4 mr-1" />
							列表
						</Link>
					</Button>
				</div>
			</header>
			<main className="mx-auto max-w-md space-y-4 p-6">
				<h1 className="text-xl font-semibold">采购发票报销审批</h1>
				<Card>
					<CardHeader>
						<CardTitle className="text-base">{summary.name}</CardTitle>
						<p className="text-sm text-muted-foreground">
							采购发票 · 过账日期 {summary.posting_date || "-"}
						</p>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="grid gap-2 text-sm">
							<div className="flex justify-between">
								<span className="text-muted-foreground">供应商</span>
								<span>{summary.supplier || "-"}</span>
							</div>
							<div className="flex justify-between">
								<span className="text-muted-foreground">垫付员工</span>
								<span>{summary.employee_name || summary.advance_employee || "-"}</span>
							</div>
							<div className="flex justify-between">
								<span className="text-muted-foreground">发票号</span>
								<span>{summary.bill_no || "-"}</span>
							</div>
							<div className="flex justify-between">
								<span className="text-muted-foreground">总金额</span>
								<span className="font-medium">
									{formatCurrency(summary.grand_total ?? 0)}
								</span>
							</div>
						</div>

						{summary.readonly && (
							<div className="rounded-md border bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
								<p className="font-medium text-foreground">
									报销审批状态：{summary.reimbursement_approval_status || "-"}
								</p>
								<p className="mt-1">
									{summary.reimbursement_approval_status === "Approved"
										? "已通过审批，无需再次操作。如需创建应付转员工日记账，请在 Desk 打开该采购发票，使用「应付转员工」按钮。"
										: summary.reimbursement_approval_status === "Rejected"
											? "已为拒绝状态，无法在此再次审批。如需调整请在 Desk 处理。"
											: "当前不可在此审批。"}
								</p>
								<Button asChild variant="secondary" className="mt-3 w-full">
									<Link to="/worker-portal/pi-reimbursement-pending">返回待审批列表</Link>
								</Button>
							</div>
						)}

						{error && <p className="text-sm text-destructive">{error}</p>}

						{!summary.readonly && showRejectInput ? (
							<div className="space-y-2">
								<Label htmlFor="remark">拒绝原因（必填）</Label>
								<Input
									id="remark"
									value={rejectRemark}
									onChange={(e) => setRejectRemark(e.target.value)}
									placeholder="请输入拒绝原因"
									className="w-full"
								/>
								<div className="flex gap-2">
									<Button
										variant="outline"
										onClick={() => setShowRejectInput(false)}
										disabled={submitting}
									>
										取消
									</Button>
									<Button
										variant="destructive"
										onClick={handleReject}
										disabled={submitting || !rejectRemark.trim()}
									>
										{submitting ? "提交中..." : "确认拒绝"}
									</Button>
								</div>
							</div>
						) : !summary.readonly ? (
							<div className="flex gap-3">
								<Button
									onClick={handleApprove}
									disabled={submitting}
									className="flex-1"
								>
									{submitting ? "提交中..." : "批准"}
								</Button>
								<Button
									variant="outline"
									onClick={handleReject}
									disabled={submitting}
									className="flex-1"
								>
									拒绝
								</Button>
							</div>
						) : null}
					</CardContent>
				</Card>
			</main>
		</div>
	)
}

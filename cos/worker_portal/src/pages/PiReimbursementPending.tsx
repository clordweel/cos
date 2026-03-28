import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft } from "lucide-react"
import {
	WpEmptyState,
	WpLoadingState,
	WpRequestFailed,
	WpSuccessState,
} from "@/components/wp-states"
import {
	listPiReimbursementPendingApproval,
	getPiSummaryForLoggedInApproval,
	approvePiLoggedIn,
	type PiReimbursementSummary,
	type PiReimbursementPendingRow,
} from "@/lib/api"
import { isCosFlutterShell } from "@/lib/clientEnv"
import {
	WpPage,
	WpPageTitle,
	WpCentered,
	wpText,
} from "@/lib/wp-layout"

function decodePiNameFromRoute(raw: string | undefined): string {
	if (!raw) return ""
	try {
		return decodeURIComponent(raw).trim()
	} catch {
		return raw.trim()
	}
}

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
			<WpCentered>
				<WpLoadingState />
			</WpCentered>
		)
	}

	return (
		<WpPage>
			{!isCosFlutterShell() && <WpPageTitle>待报销审批</WpPageTitle>}
			{error ? (
				<WpRequestFailed message={error} />
			) : null}
			{!error && rows.length === 0 ? (
				<WpEmptyState
					title="暂无待审批"
					description="当前没有符合「已提交、员工垫付、报销审批 Pending」的采购发票，或您暂无相关单据的读权限。"
				/>
			) : null}
			{!error &&
				rows.map((r) => (
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
		</WpPage>
	)
}

/** 单张 PI 审批（需登录 + 写权限） */
export function PiReimbursementPendingDetail() {
	const { piName: raw } = useParams<{ piName: string }>()
	const piName = decodePiNameFromRoute(raw)
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
			<WpCentered>
				<WpLoadingState />
			</WpCentered>
		)
	}

	if (error && !summary) {
		return (
			<WpPage narrow>
				<Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
					<Link to="/worker-portal/pi-reimbursement-pending">
						<ArrowLeft className="h-4 w-4 mr-1" />
						返回列表
					</Link>
				</Button>
				<WpRequestFailed
					message={error}
					hint="若无读权限、单据编号有误或审批已结束，将无法打开详情。"
				/>
			</WpPage>
		)
	}

	if (result) {
		return (
			<WpPage narrow>
				<WpSuccessState
					title={result === "approved" ? "已批准" : "已拒绝"}
					description="可返回列表继续处理其他单据。"
				>
					<Button asChild className="w-full">
						<Link to="/worker-portal/pi-reimbursement-pending">返回待审批列表</Link>
					</Button>
				</WpSuccessState>
			</WpPage>
		)
	}

	if (!summary) return null

	return (
		<WpPage narrow>
			<Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
				<Link to="/worker-portal/pi-reimbursement-pending">
					<ArrowLeft className="h-4 w-4 mr-1" />
					列表
				</Link>
			</Button>
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
						<div className="rounded-md border bg-muted/50 px-3 py-3 text-sm space-y-2">
							<p className="font-medium text-foreground">
								状态：{summary.reimbursement_approval_status || "-"}
							</p>
							<p className={wpText.muted}>
								{summary.reimbursement_approval_status === "Approved"
									? "已通过，无需在此再次操作。"
									: summary.reimbursement_approval_status === "Rejected"
										? "已拒绝，无法在此再次审批。"
										: "当前不可在此审批。"}
							</p>
							<Button asChild variant="secondary" className="w-full">
								<Link to="/worker-portal/pi-reimbursement-pending">返回列表</Link>
							</Button>
						</div>
					)}

					{error && <p className={wpText.error}>{error}</p>}

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
		</WpPage>
	)
}

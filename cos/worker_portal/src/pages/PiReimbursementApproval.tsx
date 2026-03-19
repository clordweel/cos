import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
	getPiSummaryForApproval,
	approvePiReimbursement,
	type PiReimbursementSummary,
} from "@/lib/api"

function formatCurrency(n: number): string {
	return new Intl.NumberFormat("zh-CN", {
		style: "currency",
		currency: "CNY",
	}).format(n)
}

export function PiReimbursementApproval() {
	const [searchParams] = useSearchParams()
	const [summary, setSummary] = useState<PiReimbursementSummary | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [result, setResult] = useState<"approved" | "rejected" | null>(null)
	const [submitting, setSubmitting] = useState(false)
	const [rejectRemark, setRejectRemark] = useState("")
	const [showRejectInput, setShowRejectInput] = useState(false)

	const query = searchParams.toString()
	const hasParams =
		searchParams.has("pi_name") &&
		searchParams.has("expiry") &&
		searchParams.has("_signature")

	useEffect(() => {
		if (!hasParams || !query) {
			setLoading(false)
			setError("链接无效，缺少必要参数")
			return
		}
		getPiSummaryForApproval(query)
			.then(setSummary)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [hasParams, query])

	const handleApprove = async () => {
		if (!query || !summary) return
		setSubmitting(true)
		setError(null)
		try {
			await approvePiReimbursement(query, "approve", "")
			setResult("approved")
		} catch (e) {
			setError((e as Error)?.message ?? "审批失败")
		} finally {
			setSubmitting(false)
		}
	}

	const handleReject = async () => {
		if (!query || !summary) return
		if (!showRejectInput) {
			setShowRejectInput(true)
			return
		}
		setSubmitting(true)
		setError(null)
		try {
			await approvePiReimbursement(query, "reject", rejectRemark)
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
				<Card>
					<CardContent className="pt-6">
						<p className="text-destructive">{error}</p>
						<p className="mt-2 text-sm text-muted-foreground">
							链接可能已过期或已被使用，请联系财务重新生成。
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
					<CardContent className="pt-6">
						<p className="text-lg font-medium">
							{result === "approved" ? "已批准" : "已拒绝"}
						</p>
						<p className="mt-1 text-sm text-muted-foreground">
							该链接已失效，无需再次操作。
						</p>
					</CardContent>
				</Card>
			</div>
		)
	}

	if (!summary) return null

	return (
		<div className="min-h-screen bg-muted/30">
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

						{error && <p className="text-sm text-destructive">{error}</p>}

						{showRejectInput ? (
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
						) : (
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
						)}
					</CardContent>
				</Card>
			</main>
		</div>
	)
}

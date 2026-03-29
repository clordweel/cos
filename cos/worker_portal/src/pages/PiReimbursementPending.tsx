import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { Link, useLocation, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Search, SearchX } from "lucide-react"
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
	type PiReimbursementLineItem,
} from "@/lib/api"
import { isCosFlutterShell } from "@/lib/clientEnv"
import {
	WpPage,
	WpPageTitle,
	WpCentered,
	wpText,
} from "@/lib/wp-layout"
import { sanitizePiRemarkHtml } from "@/lib/sanitize-html"
import { cn } from "@/lib/utils"

function decodePiNameFromRoute(raw: string | undefined): string {
	if (!raw) return ""
	let s = raw.trim()
	try {
		s = decodeURIComponent(s).trim()
	} catch {
		// 保持原样
	}
	// 少数 WebView 会把 # 后内容错误并入 path
	const hashIdx = s.indexOf("#")
	if (hashIdx >= 0) s = s.slice(0, hashIdx).trim()
	return s
}

/** useParams 异常时从 pathname 解析最后一段（与路由 `/pi-reimbursement-pending/:piName` 一致） */
function piNameFromPathname(pathname: string): string {
	const prefix = "/worker-portal/pi-reimbursement-pending/"
	if (!pathname.startsWith(prefix)) return ""
	const rest = pathname.slice(prefix.length).replace(/\/$/, "")
	if (!rest || rest.includes("/")) return ""
	return decodePiNameFromRoute(rest)
}

function formatCurrency(n: number): string {
	return new Intl.NumberFormat("zh-CN", {
		style: "currency",
		currency: "CNY",
	}).format(n)
}

type PiPendingSortKey = "posting_desc" | "amount_desc" | "amount_asc"
type PiPendingAmountFilter = "all" | "gte500" | "gte1000"

function filterAndSortPiPendingRows(
	rows: PiReimbursementPendingRow[],
	query: string,
	sort: PiPendingSortKey,
	amount: PiPendingAmountFilter,
): PiReimbursementPendingRow[] {
	const q = query.trim().toLowerCase()
	let out = rows.filter((r) => {
		if (!q) return true
		const hay = [
			r.name,
			r.supplier,
			r.employee_name ?? "",
			r.custom_advance_employee ?? "",
			r.bill_no ?? "",
			r.posting_date ?? "",
		]
			.join(" ")
			.toLowerCase()
		return hay.includes(q)
	})
	if (amount === "gte500") {
		out = out.filter((r) => (r.grand_total ?? 0) >= 500)
	}
	if (amount === "gte1000") {
		out = out.filter((r) => (r.grand_total ?? 0) >= 1000)
	}
	const sorted = [...out]
	if (sort === "posting_desc") {
		sorted.sort((a, b) =>
			(b.posting_date || "").localeCompare(a.posting_date || ""),
		)
	} else if (sort === "amount_desc") {
		sorted.sort((a, b) => (b.grand_total ?? 0) - (a.grand_total ?? 0))
	} else {
		sorted.sort((a, b) => (a.grand_total ?? 0) - (b.grand_total ?? 0))
	}
	return sorted
}

function PiDetailLineRow({ line }: { line: PiReimbursementLineItem }) {
	const [open, setOpen] = useState(false)
	const remark = (line.remark ?? "").trim()
	const hasRemark = remark.length > 0

	return (
		<div className="border-b border-border/50 last:border-0 px-2 py-2">
			<div className="flex justify-between gap-2 text-sm">
				<span className="min-w-0 flex-1 font-medium leading-snug text-foreground">
					{line.item_name?.trim() || "—"}
				</span>
				<span className="shrink-0 font-semibold tabular-nums text-foreground">
					{formatCurrency(line.amount ?? 0)}
				</span>
			</div>
			{hasRemark ? (
				<div className="mt-1.5">
					<button
						type="button"
						onClick={() => setOpen((v) => !v)}
						className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
					>
						{open ? "收起备注" : "查看备注"}
					</button>
					{open ? (
						<div
							className="pi-remark-html mt-1.5 border-l-2 border-muted pl-2 text-xs leading-relaxed text-muted-foreground [&_a]:break-all [&_a]:text-primary [&_a]:underline [&_img]:max-h-40 [&_img]:max-w-full [&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-4 [&_p]:mb-1 [&_p]:last:mb-0 [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-4"
							dangerouslySetInnerHTML={{
								__html: sanitizePiRemarkHtml(remark),
							}}
						/>
					) : null}
				</div>
			) : null}
		</div>
	)
}

/** 待报销采购发票列表（需登录） */
export function PiReimbursementPendingList() {
	const [rows, setRows] = useState<PiReimbursementPendingRow[]>([])
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [searchQuery, setSearchQuery] = useState("")
	const [sortKey, setSortKey] = useState<PiPendingSortKey>("posting_desc")
	const [amountFilter, setAmountFilter] =
		useState<PiPendingAmountFilter>("all")

	const piPendingHeaderRef = useRef<HTMLElement>(null)
	const [fixedHeaderHeightPx, setFixedHeaderHeightPx] = useState(200)

	useLayoutEffect(() => {
		const el = piPendingHeaderRef.current
		if (!el) return
		const measure = () => {
			setFixedHeaderHeightPx(el.getBoundingClientRect().height)
		}
		measure()
		const ro = new ResizeObserver(measure)
		ro.observe(el)
		return () => ro.disconnect()
	}, [rows.length, searchQuery, sortKey, amountFilter])

	/** 方案 A：Portal 挂到 body 时收缩 #worker-portal-root，避免 Frappe 壳 min-h-screen 撑高文档产生双滚动 */
	useEffect(() => {
		const el = document.getElementById("worker-portal-root")
		if (!el) return
		if (error || rows.length === 0) {
			el.classList.add("min-h-screen")
			el.style.minHeight = ""
			el.style.height = ""
			el.style.overflow = ""
			return
		}
		el.classList.remove("min-h-screen")
		el.style.minHeight = "0"
		el.style.height = "0"
		el.style.overflow = "hidden"
		return () => {
			el.classList.add("min-h-screen")
			el.style.minHeight = ""
			el.style.height = ""
			el.style.overflow = ""
		}
	}, [error, rows.length])

	useEffect(() => {
		listPiReimbursementPendingApproval(100)
			.then(setRows)
			.catch((e) => setError(e?.message ?? "加载失败"))
			.finally(() => setLoading(false))
	}, [])

	const filteredRows = useMemo(
		() => filterAndSortPiPendingRows(rows, searchQuery, sortKey, amountFilter),
		[rows, searchQuery, sortKey, amountFilter],
	)

	if (loading) {
		return (
			<WpCentered>
				<WpLoadingState />
			</WpCentered>
		)
	}

	/* 有列表数据：fixed 顶栏 + fixed 主区挂到 document.body，避免 Frappe 包裹层破坏 fixed 包含块 */
	if (!error && rows.length > 0) {
		const shellTop = "var(--cos-content-padding-top, env(safe-area-inset-top, 0px))"
		const portalChildren = (
			<>
				<header
					ref={piPendingHeaderRef}
					id="pi-pending-toolbar"
					className={cn(
						"fixed left-0 right-0 z-[100] w-full border-b border-border/40 bg-background shadow-sm",
						isCosFlutterShell() ? "pt-0" : "pt-4",
					)}
					style={{ top: shellTop }}
				>
					<div className="mx-auto w-full max-w-2xl px-4 pb-3">
						{!isCosFlutterShell() ? (
							<WpPageTitle className="mb-3">待报销采购发票</WpPageTitle>
						) : null}
						<div className="overflow-hidden rounded-2xl border border-border/50 bg-card shadow-sm">
							<div className="flex items-center gap-2 border-b border-border/35 px-3 pt-3 pb-3">
								<div
									className={cn(
										"flex min-w-0 items-center gap-2 rounded-full border border-border/70 bg-muted/40 px-3 h-10",
										isCosFlutterShell() ? "flex-1" : "w-full",
									)}
								>
									<Search
										className="h-4 w-4 shrink-0 text-muted-foreground"
										strokeWidth={2}
										aria-hidden
									/>
									<Input
										id="pi-pending-search-input"
										placeholder="单号 / 供应商 / 员工 / 发票号"
										value={searchQuery}
										onChange={(e) => setSearchQuery(e.target.value)}
										className="h-9 min-w-0 flex-1 border-0 bg-transparent p-0 text-sm shadow-none placeholder:text-muted-foreground/70 focus-visible:ring-0 focus-visible:ring-offset-0"
									/>
								</div>
								{isCosFlutterShell() ? (
									<div
										className="shrink-0 w-[76px] sm:w-[88px]"
										aria-hidden
									/>
								) : null}
							</div>

							<div
								id="pi-pending-filter-body"
								className="space-y-0 border-border/35"
							>
								<div className="border-b border-border/35 px-3 py-2.5">
									<div className="mb-1.5 flex items-center justify-between gap-2">
										<p className="text-xs font-medium text-muted-foreground">
											排序
										</p>
									</div>
									<div className="-mx-1 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
										<Button
											type="button"
											size="sm"
											variant={
												sortKey === "posting_desc" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setSortKey("posting_desc")}
										>
											过账从新到旧
										</Button>
										<Button
											type="button"
											size="sm"
											variant={
												sortKey === "amount_desc" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setSortKey("amount_desc")}
										>
											金额从高到低
										</Button>
										<Button
											type="button"
											size="sm"
											variant={
												sortKey === "amount_asc" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setSortKey("amount_asc")}
										>
											金额从低到高
										</Button>
									</div>
								</div>
								<div className="px-3 py-2.5">
									<p className="mb-1.5 text-xs font-medium text-muted-foreground">
										金额
									</p>
									<div className="-mx-1 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
										<Button
											type="button"
											size="sm"
											variant={
												amountFilter === "all" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setAmountFilter("all")}
										>
											全部
										</Button>
										<Button
											type="button"
											size="sm"
											variant={
												amountFilter === "gte500" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setAmountFilter("gte500")}
										>
											≥ ¥500
										</Button>
										<Button
											type="button"
											size="sm"
											variant={
												amountFilter === "gte1000" ? "default" : "outline"
											}
											className="h-8 shrink-0 rounded-full px-3 text-xs"
											onClick={() => setAmountFilter("gte1000")}
										>
											≥ ¥1000
										</Button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</header>

				<main
					className="fixed bottom-0 left-0 right-0 z-[90] overflow-y-auto overscroll-contain bg-muted/30 [-webkit-overflow-scrolling:touch]"
					style={{
						top: `calc(${shellTop} + ${fixedHeaderHeightPx}px)`,
					}}
				>
					<div className="mx-auto w-full max-w-2xl px-4 pb-8 pt-3">
						{filteredRows.length === 0 ? (
							<WpEmptyState
								icon={SearchX}
								title="无匹配单据"
								description="没有符合当前搜索或筛选条件的发票，可清空搜索或调整筛选。"
							>
								<Button
									type="button"
									variant="secondary"
									className="mt-2"
									onClick={() => {
										setSearchQuery("")
										setSortKey("posting_desc")
										setAmountFilter("all")
									}}
								>
									清空条件
								</Button>
							</WpEmptyState>
						) : (
							<div className="flex flex-col gap-3">
								{filteredRows.map((r) => (
									<Link
										key={r.name}
										to={`/worker-portal/pi-reimbursement-pending/${encodeURIComponent(r.name)}`}
										className="block"
									>
										<Card className="gap-0 overflow-hidden py-0 shadow-sm transition-colors hover:bg-accent/50">
											<div className="flex flex-col gap-2 px-3.5 py-2.5">
												<div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0 text-[11px] leading-none text-muted-foreground/75">
													<span className="font-mono tabular-nums tracking-tight">
														{r.name}
													</span>
													<span className="text-muted-foreground/45">·</span>
													<span>过账 {r.posting_date || "—"}</span>
												</div>
												{r.supplier ? (
													<p className="line-clamp-2 text-[11px] leading-snug text-muted-foreground/85">
														{r.supplier}
													</p>
												) : null}
												<div className="flex items-start justify-between gap-3 border-t border-border/35 pt-2">
													<div className="flex min-w-0 flex-1 flex-col gap-0.5">
														<span className="text-[10px] leading-none text-muted-foreground/65">
															垫付员工
														</span>
														<span className="truncate text-sm font-semibold leading-tight text-foreground">
															{r.employee_name ||
																r.custom_advance_employee ||
																"—"}
														</span>
													</div>
													<div className="flex shrink-0 flex-col items-end gap-0.5 text-right">
														<span className="text-[10px] leading-none text-muted-foreground/65">
															金额
														</span>
														<span className="text-base font-semibold leading-tight tabular-nums text-foreground">
															{formatCurrency(r.grand_total ?? 0)}
														</span>
													</div>
												</div>
											</div>
										</Card>
									</Link>
								))}
							</div>
						)}
					</div>
				</main>
			</>
		)

		return createPortal(portalChildren, document.body)
	}

	return (
		<WpPage>
			{!isCosFlutterShell() ? (
				<WpPageTitle>待报销采购发票</WpPageTitle>
			) : null}
			{error ? (
				<WpRequestFailed message={error} />
			) : null}
			{!error && rows.length === 0 ? (
				<WpEmptyState
					title="暂无待报销采购发票"
					description="当前没有符合「已提交、员工垫付、报销审批 Pending」的采购发票，或您暂无相关单据的读权限。"
				/>
			) : null}
		</WpPage>
	)
}

/** 单张 PI 审批（需登录 + 写权限） */
export function PiReimbursementPendingDetail() {
	const { piName: raw } = useParams<{ piName: string }>()
	const { pathname } = useLocation()
	const piName =
		decodePiNameFromRoute(raw) || piNameFromPathname(pathname)
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
				{!isCosFlutterShell() ? (
					<Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
						<Link to="/worker-portal/pi-reimbursement-pending">
							<ArrowLeft className="h-4 w-4 mr-1" />
							返回列表
						</Link>
					</Button>
				) : null}
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
						<Link to="/worker-portal/pi-reimbursement-pending">返回列表</Link>
					</Button>
				</WpSuccessState>
			</WpPage>
		)
	}

	if (!summary) return null

	return (
		<WpPage narrow>
			{!isCosFlutterShell() ? (
				<Button variant="ghost" size="sm" asChild className="-ml-2 w-fit">
					<Link to="/worker-portal/pi-reimbursement-pending">
						<ArrowLeft className="h-4 w-4 mr-1" />
						列表
					</Link>
				</Button>
			) : null}
			<Card className="gap-0 py-0 shadow-sm">
				<CardHeader className="space-y-1 px-3 py-2.5 pb-2">
					<div className="flex flex-wrap items-center gap-x-1.5 text-[11px] leading-tight text-muted-foreground/75">
						<span className="font-mono tabular-nums tracking-tight">{summary.name}</span>
						<span className="text-muted-foreground/45">·</span>
						<span>过账 {summary.posting_date || "—"}</span>
					</div>
					<p className="line-clamp-2 text-[11px] leading-snug text-muted-foreground/85">
						采购发票 · {summary.supplier || "—"}
					</p>
				</CardHeader>
				<CardContent className="space-y-3 px-3 pb-3 pt-0">
					<div className="flex items-end justify-between gap-3 border-b border-border/40 pb-3">
						<div className="min-w-0 flex-1">
							<p className="text-[10px] text-muted-foreground/65">垫付员工</p>
							<p className="mt-0.5 truncate text-sm font-semibold text-foreground">
								{summary.employee_name || summary.advance_employee || "—"}
							</p>
						</div>
						<div className="shrink-0 text-right">
							<p className="text-[10px] text-muted-foreground/65">总金额</p>
							<p className="mt-0.5 text-base font-semibold tabular-nums text-foreground">
								{formatCurrency(summary.grand_total ?? 0)}
							</p>
						</div>
					</div>

					<div className="flex justify-between gap-2 text-xs text-muted-foreground">
						<span>发票号</span>
						<span className="max-w-[65%] break-all text-right text-foreground/80">
							{summary.bill_no || "—"}
						</span>
					</div>

					<div className="overflow-hidden rounded-md border border-border/60 bg-muted/25">
						<p className="border-b border-border/50 bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
							物料明细
						</p>
						{summary.items && summary.items.length > 0 ? (
							summary.items.map((line, i) => (
								<PiDetailLineRow key={`${line.item_name}-${i}`} line={line} />
							))
						) : (
							<p className="px-3 py-3 text-xs text-muted-foreground">暂无明细</p>
						)}
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

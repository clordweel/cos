import { normalizeFrappeRpcErrorMessage } from "@/lib/frappe-rpc-error"

const TOKEN_KEY = "cos_worker_portal_token"

/** 纯 Cookie 会话的 POST 需带 CSRF；Bearer wpt. 由服务端 patch 豁免。 */
function readCookie(name: string): string | null {
	if (typeof document === "undefined") return null
	const prefix = `${name}=`
	const parts = document.cookie.split(";")
	for (const part of parts) {
		const s = part.trim()
		if (s.startsWith(prefix)) {
			return decodeURIComponent(s.slice(prefix.length))
		}
	}
	return null
}

export function getApiBase(): string {
	return (
		(typeof window !== "undefined" && window.__WORKER_PORTAL_CONFIG__?.apiBase) ||
		""
	)
}

export function getToken(): string | null {
	if (typeof window === "undefined") return null
	// 必须优先 localStorage：壳通过 hash 写入的 wpt 在这里；HTML 里 initialToken 常为 null，
	// 若反客为主用 initialToken，易被占位/错误注入覆盖，导致列表能带旧缓存、详情等新请求丢 Bearer。
	const ls = localStorage.getItem(TOKEN_KEY)
	if (ls != null && ls.trim() !== "") return ls.trim()
	const init = window.__WORKER_PORTAL_CONFIG__?.initialToken
	if (typeof init === "string" && init.trim() !== "") return init.trim()
	return null
}

export function setToken(token: string): void {
	localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
	localStorage.removeItem(TOKEN_KEY)
}

export async function apiRequest<T>(
	method: string,
	path: string,
	body?: unknown
): Promise<T> {
	const base = getApiBase()
	const token = getToken()
	const url = base ? `${base}${path}` : path
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
	}
	if (token) {
		headers["Authorization"] = `Bearer ${token}`
	} else if (method !== "GET" && method !== "HEAD") {
		const csrf = readCookie("csrf_token")
		if (csrf) headers["X-Frappe-CSRF-Token"] = csrf
	}
	const res = await fetch(url, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined,
		credentials: "same-origin",
		// WebView/企业网关偶发缓存或丢弃带长 query 的 GET，导致详情误判「采购发票不存在」
		cache: "no-store",
	})
	const data = (await res.json().catch(() => ({}))) as Record<string, unknown>
	if (!res.ok) {
		throw new Error(normalizeFrappeRpcErrorMessage(data))
	}
	return data as T
}

export async function login(username: string, password: string) {
	const base = getApiBase()
	const url = base ? `${base}/api/method/cos.worker_portal_api.login_for_token` : "/api/method/cos.worker_portal_api.login_for_token"
	const res = await fetch(url, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ usr: username, pwd: password }),
		credentials: "same-origin",
		cache: "no-store",
	})
	const data = (await res.json()) as Record<string, unknown>
	if (data.exc) {
		throw new Error(normalizeFrappeRpcErrorMessage(data) || "登录失败")
	}
	// Frappe 将方法返回值放在 message 中
	return (data.message ?? data) as { token: string; user: string }
}

export async function getLoggedUser(): Promise<string> {
	const base = getApiBase()
	const token = getToken()
	const url = base ? `${base}/api/method/cos.worker_portal_api.get_logged_user` : "/api/method/cos.worker_portal_api.get_logged_user"
	const headers: Record<string, string> = {}
	if (token) headers["Authorization"] = `Bearer ${token}`
	const res = await fetch(url, {
		credentials: "same-origin",
		headers,
		cache: "no-store",
	})
	const data = await res.json().catch(() => ({}))
	const msg = data.message ?? data
	return typeof msg === "string" ? msg : "Guest"
}

// 已批待 JE 已从 Worker Portal 移除；list_employee_advance_pending / get_purchase_invoice_detail /
// create_payable_transfer_je 仍可在服务端供 Desk 等调用，前端不再封装。

// --- 采购发票报销链接审批（免登录）---

export interface PiReimbursementLineItem {
	/** 物料名称（或物料编码兜底） */
	item_name: string
	amount: number
	/** 行备注（Purchase Invoice Item.description） */
	remark?: string | null
}

export interface PiReimbursementSummary {
	name: string
	supplier: string
	grand_total: number
	advance_employee: string
	employee_name: string | null
	bill_no: string
	posting_date: string | null
	/** 发票明细行 */
	items?: PiReimbursementLineItem[]
	/** 服务端：非 Pending 时为 true，仅展示不可再批 */
	readonly?: boolean
	reimbursement_approval_status?: string
}

export interface PiReimbursementApproveResult {
	success: boolean
	status: string
	message: string
}

async function guestFetch<T>(path: string, init?: RequestInit): Promise<{ message?: T }> {
	const base = getApiBase()
	const url = base ? `${base}${path}` : path
	const res = await fetch(url, {
		...init,
		credentials: "same-origin",
		cache: "no-store",
	})
	const data = (await res.json().catch(() => ({}))) as Record<string, unknown>
	if (data.exc) throw new Error(normalizeFrappeRpcErrorMessage(data))
	if (!res.ok) throw new Error(normalizeFrappeRpcErrorMessage(data) || `HTTP ${res.status}`)
	return data
}

export async function getPiSummaryForApproval(query: string): Promise<PiReimbursementSummary> {
	const data = await guestFetch<PiReimbursementSummary>(
		`/api/method/cos.cos_accounts.pi_reimbursement_approval.get_pi_summary_for_approval?${query}`
	)
	return data.message as PiReimbursementSummary
}

export async function approvePiReimbursement(
	query: string,
	action: "approve" | "reject",
	remark = ""
): Promise<PiReimbursementApproveResult> {
	const params = new URLSearchParams(query)
	const body = new URLSearchParams({
		token: query.startsWith("?") ? query : `?${query}`,
		action,
		remark,
	})
	const data = await guestFetch<PiReimbursementApproveResult>(
		"/api/method/cos.cos_accounts.pi_reimbursement_approval.approve_pi",
		{
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: body.toString(),
		}
	)
	return data.message as PiReimbursementApproveResult
}

// --- 采购发票报销审批（Worker Portal 已登录）---

export interface PiReimbursementPendingRow {
	name: string
	supplier: string
	custom_advance_employee: string | null
	employee_name?: string | null
	grand_total: number
	posting_date: string | null
	bill_no: string | null
	custom_reimbursement_approval_status?: string | null
}

/** 与 worker_portal_api.list_pi_reimbursement_pending_approval 的 tab 一致 */
export type PiReimbursementListTab = "all" | "pending" | "approved" | "rejected"

export async function listPiReimbursementPendingApproval(
	limit = 50,
	tab: PiReimbursementListTab = "pending"
): Promise<PiReimbursementPendingRow[]> {
	const t = encodeURIComponent(tab)
	const res = await apiRequest<
		{ message?: PiReimbursementPendingRow[] } | PiReimbursementPendingRow[]
	>(
		"GET",
		`/api/method/cos.worker_portal_api.list_pi_reimbursement_pending_approval?limit=${limit}&tab=${t}`
	)
	return Array.isArray(res) ? res : (res?.message ?? [])
}

export async function getPiSummaryForLoggedInApproval(
	piName: string
): Promise<PiReimbursementSummary> {
	// 统一 POST + JSON：避免 WebView/代理对 GET query 异常；无 wpt 时 apiRequest 会带 Cookie CSRF。
	// URL 上再带一份 pi_name，与服务端多重解析形成兜底。
	const q = encodeURIComponent(piName)
	const res = await apiRequest<{ message?: PiReimbursementSummary } | PiReimbursementSummary>(
		"POST",
		`/api/method/cos.cos_accounts.pi_reimbursement_approval.get_pi_summary_for_logged_in_approval?pi_name=${q}`,
		{ pi_name: piName },
	)
	if (res && typeof res === "object" && "message" in res && res.message !== undefined) {
		return res.message as PiReimbursementSummary
	}
	return res as PiReimbursementSummary
}

export async function approvePiLoggedIn(
	piName: string,
	action: "approve" | "reject",
	remark = ""
): Promise<PiReimbursementApproveResult> {
	const res = await apiRequest<{ message?: PiReimbursementApproveResult }>(
		"POST",
		"/api/method/cos.cos_accounts.pi_reimbursement_approval.approve_pi_logged_in",
		{ pi_name: piName, action, remark }
	)
	if (res && typeof res === "object" && "message" in res && res.message !== undefined) {
		return res.message as PiReimbursementApproveResult
	}
	return res as PiReimbursementApproveResult
}

const TOKEN_KEY = "cos_worker_portal_token"

export function getApiBase(): string {
	return (
		(typeof window !== "undefined" && window.__WORKER_PORTAL_CONFIG__?.apiBase) ||
		""
	)
}

export function getToken(): string | null {
	return (
		typeof window !== "undefined" && window.__WORKER_PORTAL_CONFIG__?.initialToken
			? window.__WORKER_PORTAL_CONFIG__.initialToken
			: localStorage.getItem(TOKEN_KEY)
	)
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
	}
	const res = await fetch(url, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined,
		credentials: "same-origin",
	})
	const data = await res.json().catch(() => ({}))
	if (!res.ok) {
		throw new Error(data.message || data.exc || "Request failed")
	}
	return data
}

export async function login(username: string, password: string) {
	const base = getApiBase()
	const url = base ? `${base}/api/method/cos.worker_portal_api.login_for_token` : "/api/method/cos.worker_portal_api.login_for_token"
	const res = await fetch(url, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ usr: username, pwd: password }),
		credentials: "same-origin",
	})
	const data = await res.json()
	if (data.exc) {
		throw new Error(data.message || "登录失败")
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
	const res = await fetch(url, { credentials: "same-origin", headers })
	const data = await res.json().catch(() => ({}))
	const msg = data.message ?? data
	return typeof msg === "string" ? msg : "Guest"
}

// --- 采购垫付报销审批 ---

export interface EmployeeAdvanceItem {
	name: string
	supplier: string
	custom_advance_employee: string | null
	employee_name?: string | null
	grand_total: number
	posting_date: string | null
	custom_payable_transfer_je: string | null
}

export async function listEmployeeAdvancePending(limit = 50): Promise<EmployeeAdvanceItem[]> {
	const res = await apiRequest<{ message?: EmployeeAdvanceItem[] } | EmployeeAdvanceItem[]>(
		"GET",
		`/api/method/cos.worker_portal_api.list_employee_advance_pending?limit=${limit}`
	)
	return Array.isArray(res) ? res : (res?.message ?? [])
}

export interface PurchaseInvoiceDetail {
	name: string
	supplier: string
	custom_advance_employee: string | null
	employee_name?: string | null
	grand_total: number
	posting_date: string | null
	custom_payable_transfer_je: string | null
	custom_employee_reimbursed: string
	items: { item_code: string; item_name: string; qty: number; rate: number; amount: number }[]
}

export async function getPurchaseInvoiceDetail(name: string): Promise<PurchaseInvoiceDetail> {
	const res = await apiRequest<PurchaseInvoiceDetail>(
		"GET",
		`/api/method/cos.worker_portal_api.get_purchase_invoice_detail?name=${encodeURIComponent(name)}`
	)
	return res?.message ?? res
}

export async function createPayableTransferJe(docname: string): Promise<{ message?: unknown }> {
	return apiRequest("POST", "/api/method/cos.worker_portal_api.create_payable_transfer_je", {
		docname,
	})
}

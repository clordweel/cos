/**
 * Frappe RPC 失败时 JSON 里的 message 常为 Traceback 字符串或字符串数组，
 * 直接用作 Error.message 会把整段堆栈展示给用户。此处提取可读文案。
 */
function parseFrappeServerMessages(raw: unknown): string | null {
	if (typeof raw !== "string" || !raw.trim()) return null
	try {
		const arr = JSON.parse(raw) as unknown[]
		if (!Array.isArray(arr)) return null
		for (const entry of arr) {
			if (typeof entry !== "string") continue
			try {
				const o = JSON.parse(entry) as { message?: string }
				if (typeof o.message === "string" && o.message.trim()) return o.message.trim()
			} catch {
				continue
			}
		}
	} catch {
		return null
	}
	return null
}

function extractFromTracebackBlock(s: string): string | null {
	const trimmed = s.trim()
	if (!trimmed.includes("Traceback (most recent call last)")) return null
	const lines = trimmed.split("\n")
	for (let i = lines.length - 1; i >= 0; i--) {
		const line = lines[i].trim()
		const m = line.match(/frappe\.exceptions\.\w+:\s*(.+)$/)
		if (m) return m[1].trim()
		const m2 = line.match(/^[A-Za-z][\w]*Error:\s*(.+)$/)
		if (m2) return m2[1].trim()
	}
	return null
}

function normalizeMessageField(msg: unknown): string | null {
	if (msg == null) return null

	if (typeof msg === "string") {
		const t = msg.trim()
		if (t.startsWith("[")) {
			try {
				const parsed = JSON.parse(t) as unknown
				const inner = normalizeMessageField(parsed)
				if (inner) return inner
			} catch {
				/* 非 JSON，按普通字符串处理 */
			}
		}
		const fromTb = extractFromTracebackBlock(t)
		if (fromTb) return fromTb
		return t.length > 800 ? null : t
	}

	if (Array.isArray(msg)) {
		for (const item of msg) {
			if (typeof item !== "string") continue
			try {
				const o = JSON.parse(item) as { message?: string }
				if (typeof o.message === "string" && o.message.trim()) return o.message.trim()
			} catch {
				const fromTb = extractFromTracebackBlock(item)
				if (fromTb) return fromTb
			}
		}
	}

	return null
}

export function normalizeFrappeRpcErrorMessage(data: Record<string, unknown>): string {
	const fromSm = parseFrappeServerMessages(data._server_messages)
	if (fromSm) return fromSm

	const fromMsg = normalizeMessageField(data.message)
	if (fromMsg) return fromMsg

	const fromExc = typeof data.exc === "string" ? extractFromTracebackBlock(data.exc) : null
	if (fromExc) return fromExc

	if (typeof data.exc_type === "string" && data.exc_type.trim()) {
		return `${data.exc_type}（请求失败）`
	}

	return "Request failed"
}

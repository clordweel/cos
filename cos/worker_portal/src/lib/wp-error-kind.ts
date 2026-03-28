/** 根据 Frappe / 浏览器常见文案归类，用于展示对应空态与引导文案 */

export type WpErrorKind =
	| "permission"
	| "not_found"
	| "auth"
	| "invalid_link"
	| "network"
	| "unknown"

export function classifyWorkerPortalError(message: string): WpErrorKind {
	const raw = message || ""
	const m = raw.toLowerCase()

	if (
		/无权限|没有权限|权限不足|无权|not permitted|permission|forbidden|\b403\b/i.test(
			raw,
		)
	) {
		return "permission"
	}
	if (
		/不存在|找不到|未找到|not found|does not exist|doesn't exist|nocreatepermission/i.test(
			raw,
		) ||
		/\b404\b/.test(raw)
	) {
		return "not_found"
	}
	if (
		/登录|guest|未登录|token|凭据|\b401\b|authentication|unauthoriz|session|user\s+none\s+not\s+found/i.test(
			raw,
		)
	) {
		return "auth"
	}
	if (/链接|参数|无效|过期|expired|签名|signature|缺少必要/i.test(raw)) {
		return "invalid_link"
	}
	if (/网络|failed to fetch|network|load failed|timeout|连接/i.test(raw)) {
		return "network"
	}
	if (m.includes("fetch")) return "network"

	return "unknown"
}

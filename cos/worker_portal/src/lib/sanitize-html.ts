import DOMPurify from "dompurify"

/**
 * 采购发票行备注（ERP 富文本 / 带 HTML），用于 React 内安全渲染。
 * 去掉脚本、事件处理器等；保留常见排版标签。
 */
export function sanitizePiRemarkHtml(html: string): string {
	const s = (html ?? "").trim()
	if (!s) return ""
	return DOMPurify.sanitize(s, {
		USE_PROFILES: { html: true },
	})
}

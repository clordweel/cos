# Copyright (c) 2026, COS and contributors
"""从 print_format/stock-reconciliation-standard 同步模板到 Print Format「库存调账 - 标准」。

用法（在 dev 服务器上）:
  bench --site cos-dev.junhai.work execute cos.scripts.sync_stock_reconciliation_print_format.sync

若 Print Format 不存在则自动创建；同步后执行 bench export-fixtures，再提交 cos/fixtures/print_format.json。
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	"""获取 print_format 目录路径。get_app_path 返回 apps/cos/cos，print_format 在 apps/cos/。"""
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent  # apps/cos
	return app_root / "print_format" / "stock-reconciliation-standard"


def sync(site: str | None = None) -> dict:
	"""从 print_format/stock-reconciliation-standard 读取 template.html 和 styles.css，更新或创建 Print Format。"""
	frappe.connect(site=site)
	base = _get_print_format_dir()

	template_path = base / "template.html"
	css_path = base / "styles.css"

	if not template_path.exists():
		raise FileNotFoundError(f"模板不存在: {template_path}")
	if not css_path.exists():
		raise FileNotFoundError(f"样式文件不存在: {css_path}")

	html = template_path.read_text(encoding="utf-8")
	css = css_path.read_text(encoding="utf-8")

	name = "库存调账 - 标准"
	existed = frappe.db.exists("Print Format", name)
	if existed:
		doc = frappe.get_doc("Print Format", name)
		doc.html = html
		doc.css = css
		doc.module = "COS Stock"
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": name,
				"doc_type": "Stock Reconciliation",
				"module": "COS Stock",
				"print_format_type": "Jinja",
				"custom_format": 1,
				"html": html,
				"css": css,
				"standard": "No",
			}
		)
		doc.insert()
	frappe.db.commit()

	return {"updated": name, "created": not bool(existed), "html_len": len(html), "css_len": len(css)}

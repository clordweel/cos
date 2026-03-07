# Copyright (c) 2026, COS and contributors
"""从 print_format/sale-order-standard 同步模板到 Print Format「销售订单 - 标准」。

用法:
  bench --site junhai.local execute cos.scripts.sync_sale_order_print_format.sync
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "sale-order-standard"


def sync(site: str | None = None) -> dict:
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
	name = "销售订单 - 标准"
	existed = frappe.db.exists("Print Format", name)
	if existed:
		doc = frappe.get_doc("Print Format", name)
		doc.html = html
		doc.css = css
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": name,
				"doc_type": "Sales Order",
				"module": "COS Share",
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

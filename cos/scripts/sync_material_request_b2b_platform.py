# Copyright (c) 2026, COS and contributors
"""从 print_format/material-request-b2b-platform 同步模板到 Print Format「物料需求 - B2B平台报价」。

适用于京东工品汇等工业电商：扁平表头、单列字段，便于 OCR / 表格识别与批量询价。

用法:
  bench --site <site> execute cos.scripts.sync_material_request_b2b_platform.sync
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "material-request-b2b-platform"


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
	name = "物料需求 - B2B平台报价"
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
				"doc_type": "Material Request",
				"module": "COS Stock",
				"print_format_type": "Jinja",
				"custom_format": 1,
				"html": html,
				"css": css,
				"standard": "No",
				"default_print_language": "zh",
			}
		)
		doc.insert()
	frappe.db.commit()
	return {"updated": name, "created": not bool(existed), "html_len": len(html), "css_len": len(css)}

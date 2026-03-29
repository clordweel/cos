# Copyright (c) 2026, COS and contributors
"""从 print_format/supplier-quotation-external-no-price 同步到 Print Format「供应商报价单 - 外部（无价格）」。

价税列与汇总区保留版面，始终留空供供应商填写（不打印系统内已有单价/合计）。

用法:
  bench --site <site> execute cos.scripts.sync_supplier_quotation_external_no_price.sync
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "supplier-quotation-external-no-price"


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
	name = "供应商报价单 - 外部（无价格）"
	# 与「供应商报价单 - 外部」fixture 对齐：Chrome(Puppeteer) 与 wkhtmltopdf 对表格/CSS 渲染差异大，
	# 未设置时默认走 wkhtmltopdf，易出现列宽错乱、换行异常等「PDF 渲染错误」。
	print_settings = {
		"pdf_generator": "chrome",
		"page_number": "Hide",
		"default_print_language": "zh",
		"font_size": 14,
		"margin_top": 15.0,
		"margin_bottom": 15.0,
		"margin_left": 15.0,
		"margin_right": 15.0,
	}
	existed = frappe.db.exists("Print Format", name)
	if existed:
		doc = frappe.get_doc("Print Format", name)
		doc.html = html
		doc.css = css
		for key, val in print_settings.items():
			setattr(doc, key, val)
		doc.save()
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": name,
				"doc_type": "Supplier Quotation",
				"module": "COS Buying",
				"print_format_type": "Jinja",
				"custom_format": 1,
				"html": html,
				"css": css,
				"standard": "No",
				**print_settings,
			}
		)
		doc.insert()
	frappe.db.commit()
	return {"updated": name, "created": not bool(existed), "html_len": len(html), "css_len": len(css)}

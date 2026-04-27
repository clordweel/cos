# Copyright (c) 2026, COS and contributors
"""从 print_format/payment-request-standard 同步到收付款申请 Print Format。

用法（在服务器上）:
  bench --site junhai.local execute cos.scripts.sync_payment_request_print_format.sync

说明：若站点中 Print Format 显示名称不是「收付款申请 - 标准」，请改下方 name 后执行。
同步后可选：bench export-fixtures 合并入 cos/fixtures/print_format.json（若纳入 fixture 维护流程）。
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "payment-request-standard"


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
	name = "收付款申请 - 标准"
	if not frappe.db.exists("Print Format", name):
		frappe.throw(f"Print Format「{name}」不存在，请先在站点中创建并命名与脚本一致，或改脚本中 name 后再执行")
	doc = frappe.get_doc("Print Format", name)
	doc.html = html
	doc.css = css
	doc.module = "COS Share"
	doc.save()
	frappe.db.commit()
	return {"updated": name, "html_len": len(html), "css_len": len(css)}

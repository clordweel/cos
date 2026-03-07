# Copyright (c) 2026, COS and contributors
"""从 print_format/purchase-order-standard 同步模板到 Print Format「采购订单 - 标准」。

用法（在 dev 服务器上）:
  bench --site cos-dev.junhai.work execute cos.scripts.sync_purchase_order_print_format.sync

同步后执行 bench export-fixtures，再提交 cos/fixtures/print_format.json 到仓库。
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	"""获取 print_format 目录路径（cos app 根目录下）。"""
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "purchase-order-standard"


def sync(site: str | None = None) -> dict:
	"""从 print_format/purchase-order-standard 读取 template.html 和 styles.css，更新 Print Format。"""
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

	name = "采购订单 - 标准"
	if not frappe.db.exists("Print Format", name):
		frappe.throw(f"Print Format「{name}」不存在，请先在 dev 中创建")

	doc = frappe.get_doc("Print Format", name)
	doc.html = html
	doc.css = css
	doc.module = "COS Share"  # 确保 export-fixtures 能导出
	doc.save()
	frappe.db.commit()

	return {"updated": name, "html_len": len(html), "css_len": len(css)}

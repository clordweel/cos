# Copyright (c) 2026, COS and contributors
"""从 print_format/contract-and-terms-* 等目录同步采购/销售合同类打印格式（服务器侧灌库）。

日常开发与版本管理请以 `cos/fixtures/print_format.json` 为准；本脚本用于 bench 已连仓库时
从遗留目录写回数据库，变更仍需合并进 fixture 再提交。

包含：
- 「采购订单 - 合同 - 通用」← contract-and-terms-purchase
- 「销售订单 - 合同 - 通用」← contract-and-terms-sales
- 「采购订单 - 合同 - 工业产品 A4」← contract-industrial-product-purchase-a4

用法（在 dev 服务器上）:
  bench --site cos-dev.junhai.work execute cos.scripts.sync_contract_po_so_print_formats.sync

同步后如需纳入仓库：bench export-fixtures，再提交 cos/fixtures/print_format.json。
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir(subdir: str) -> Path:
	"""print_format 目录位于 cos app 根目录旁。"""
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / subdir


def sync_one_print_format(print_format_name: str, subdir: str) -> dict:
	"""从仓库目录同步单个 Print Format 的 HTML/CSS。"""
	base = _get_print_format_dir(subdir)
	template_path = base / "template.html"
	css_path = base / "styles.css"
	if not template_path.exists():
		raise FileNotFoundError(f"模板不存在: {template_path}")
	if not css_path.exists():
		raise FileNotFoundError(f"样式文件不存在: {css_path}")
	html = template_path.read_text(encoding="utf-8")
	css = css_path.read_text(encoding="utf-8")
	if not frappe.db.exists("Print Format", print_format_name):
		frappe.throw(f"Print Format「{print_format_name}」不存在，请先在站点中创建")
	doc = frappe.get_doc("Print Format", print_format_name)
	doc.html = html
	doc.css = css
	doc.module = "COS Share"
	doc.save()
	frappe.db.commit()
	return {"updated": print_format_name, "html_len": len(html), "css_len": len(css)}


def sync(site: str | None = None) -> list[dict]:
	"""同步采购/销售合同「通用」及工业产品 A4 模板。"""
	# migrate / 补丁内已连接 DB 时禁止再 connect，否则未提交的 insert 对新连接不可见
	if not frappe.db:
		frappe.connect(site=site)
	elif site is not None and getattr(frappe.local, "site", None) != site:
		frappe.connect(site=site)
	pairs = (
		("采购订单 - 合同 - 通用", "contract-and-terms-purchase"),
		("销售订单 - 合同 - 通用", "contract-and-terms-sales"),
		("采购订单 - 合同 - 工业产品 A4", "contract-industrial-product-purchase-a4"),
	)
	results = []
	for print_format_name, subdir in pairs:
		results.append(sync_one_print_format(print_format_name, subdir))
	return results

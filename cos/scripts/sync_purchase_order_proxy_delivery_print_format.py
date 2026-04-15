# Copyright (c) 2026, COS and contributors
"""从 print_format/purchase-order-proxy-delivery 同步到「采购订单 - 直发单」。

用法（在 dev 服务器上）:
  bench --site cos-dev.junhai.work execute cos.scripts.sync_purchase_order_proxy_delivery_print_format.sync

首次部署：fixtures 已含该 Print Format；本脚本用于从仓库文件覆盖站点中的 HTML/CSS。
若站点尚无该记录，将按「采购订单 - 标准」的元数据插入一条新记录后再写入模板。
模板含直发单标题、委托方、收货信息、项目客户、物料行仓库、数量格式与页脚声明；迁移补丁见 resync_*、rename_*、v4–v6。
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _get_print_format_dir() -> Path:
	"""print_format 目录位于 cos app 根目录旁。"""
	pkg_path = Path(frappe.get_app_path("cos"))
	app_root = pkg_path.parent
	return app_root / "print_format" / "purchase-order-proxy-delivery"


def sync(site: str | None = None) -> dict:
	"""同步「采购订单 - 直发单」模板（创建或更新）。"""
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
	name = "采购订单 - 直发单"
	if frappe.db.exists("Print Format", name):
		doc = frappe.get_doc("Print Format", name)
		doc.html = html
		doc.css = css
		doc.save()
		frappe.db.commit()
		return {"updated": name, "html_len": len(html), "css_len": len(css)}
	if not frappe.db.exists("Print Format", "采购订单 - 标准"):
		frappe.throw("请先存在 Print Format「采购订单 - 标准」，以便复制元数据创建「采购订单 - 直发单」")
	src = frappe.get_doc("Print Format", "采购订单 - 标准")
	meta = src.as_dict()
	for k in ("name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"):
		meta.pop(k, None)
	meta["name"] = name
	meta["doctype"] = "Print Format"
	meta["html"] = html
	meta["css"] = css
	new_doc = frappe.get_doc(meta)
	new_doc.insert()
	frappe.db.commit()
	return {"inserted": name, "html_len": len(html), "css_len": len(css)}

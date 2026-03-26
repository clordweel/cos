# Copyright (c) 2026, COS and contributors
"""为 Supplier Quotation Item 增加 custom_supplier_provides_drawing（从 Item 带出），并刷新外部打印模板。"""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Supplier Quotation Item"):
		return

	name = "Supplier Quotation Item-custom_supplier_provides_drawing"
	if not frappe.db.exists("Custom Field", name):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Supplier Quotation Item",
				"module": "COS Buying",
				"fieldname": "custom_supplier_provides_drawing",
				"fieldtype": "Check",
				"label": "是否供应商提供图纸",
				"insert_after": "description",
				"fetch_from": "item_code.custom_supplier_provides_drawing",
				"fetch_if_empty": 1,
				"default": "0",
				"description": "勾选表示该行物料由供应商提供图纸；可从物料主数据自动带出；提交后允许修改",
				"allow_on_submit": 1,
				"in_list_view": 1,
				"print_hide": 0,
				"print_hide_if_no_value": 0,
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Supplier Quotation")

	from cos.scripts.sync_material_request_external import sync as sync_mr_external
	from cos.scripts.sync_supplier_quotation_external import sync as sync_sq_external

	for sync_fn in (sync_mr_external, sync_sq_external):
		try:
			sync_fn()
		except FileNotFoundError:
			frappe.log_error(
				title=f"Print Format sync skipped: {sync_fn.__module__}",
				message="template or styles.css missing",
			)

	frappe.db.commit()

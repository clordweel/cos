# Copyright (c) 2026, COS and contributors
"""移除已废弃的 Purchase Order 字段 custom_print_item_description（已由 custom_is_print_item_remarks 替代）。

删除 Custom Field 元数据并尝试删除数据库列（若仍存在）。"""

from __future__ import annotations

import frappe


def execute():
	name = "Purchase Order-custom_print_item_description"
	col = "custom_print_item_description"

	if frappe.db.exists("Custom Field", name):
		frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache(doctype="Purchase Order")

	if frappe.db.has_column("Purchase Order", col):
		try:
			frappe.db.sql(f"ALTER TABLE `tabPurchase Order` DROP COLUMN `{col}`")
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(title="remove_po_custom_print_item_description: drop column", message=str(e))

	frappe.clear_cache(doctype="Purchase Order")

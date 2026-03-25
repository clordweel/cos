"""PO「付款」Tab 的 insert_after 锚点兼容 v15：v15 无 item_wise_tax_details，改为 other_charges_calculation。"""

from __future__ import annotations

import frappe


def execute():
	name = "Purchase Order-custom_tab_payment"
	if not frappe.db.exists("Custom Field", name):
		return
	row = frappe.db.get_value(
		"Custom Field",
		name,
		["insert_after", "fieldtype", "label"],
		as_dict=True,
	)
	if not row or row.get("fieldtype") != "Tab Break":
		return
	if row.get("insert_after") == "other_charges_calculation":
		return
	frappe.db.set_value("Custom Field", name, "insert_after", "other_charges_calculation")
	frappe.clear_cache(doctype="Purchase Order")
	frappe.db.commit()

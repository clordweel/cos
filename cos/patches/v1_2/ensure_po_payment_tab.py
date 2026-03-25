"""确保采购订单「付款」Tab 存在且锚点有效。

根因说明：
1. 仅修正 insert_after 的 patch 在「Custom Field 行不存在」时不做事，prod 若未同步到
   Purchase Order-custom_tab_payment，界面永远没有「付款」Tab。
2. insert_after 若指向当前 ERPNext 版本中不存在的标准字段，Frappe 表单可能不渲染该 Tab。

本 patch 幂等：补建 Tab、选用首个存在的标准字段作锚点、把员工垫付 Section 挂到 Tab 下。
"""

from __future__ import annotations

import frappe


def _first_existing_anchor(meta) -> str | None:
	for fname in (
		"other_charges_calculation",
		"item_wise_tax_details",
		"sec_tax_breakup",
		"advance_paid",
		"address_and_contact_tab",
		"terms_tab",
	):
		if meta.get_field(fname):
			return fname
	return None


def execute():
	frappe.clear_cache(doctype="Purchase Order")
	meta = frappe.get_meta("Purchase Order", cached=False)
	anchor = _first_existing_anchor(meta)
	if not anchor:
		return

	tab_name = "Purchase Order-custom_tab_payment"
	section_name = "Purchase Order-custom_section_employee_advance_reimbursement"

	if frappe.db.exists("Custom Field", tab_name):
		frappe.db.set_value("Custom Field", tab_name, "insert_after", anchor)
		frappe.db.set_value("Custom Field", tab_name, "hidden", 0)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Purchase Order",
				"fieldname": "custom_tab_payment",
				"fieldtype": "Tab Break",
				"label": "付款",
				"module": "COS Accounts",
				"insert_after": anchor,
				"hidden": 0,
			}
		)
		doc.insert(ignore_permissions=True)

	if frappe.db.exists("Custom Field", section_name):
		cur = frappe.db.get_value("Custom Field", section_name, "insert_after")
		if cur != "custom_tab_payment":
			frappe.db.set_value("Custom Field", section_name, "insert_after", "custom_tab_payment")

	frappe.clear_cache(doctype="Purchase Order")
	frappe.db.commit()

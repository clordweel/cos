# Copyright (c) 2026, COS and contributors
"""采购订单：新增「是否打印物料备注 (描述)」(custom_is_print_item_remarks)，置于 custom_is_print_terms 之后；

从旧字段 custom_print_item_description 迁移取值后隐藏旧字段（界面仅保留新勾选框）。"""

from __future__ import annotations

import frappe


def _anchor_fieldname() -> str:
	if frappe.db.exists("Custom Field", {"dt": "Purchase Order", "fieldname": "custom_is_print_terms"}):
		return "custom_is_print_terms"
	return "custom_hide_contract_seal"


def execute():
	new_name = "Purchase Order-custom_is_print_item_remarks"
	old_name = "Purchase Order-custom_print_item_description"
	target_after = _anchor_fieldname()

	if not frappe.db.exists("Custom Field", new_name):
		doc = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"name": new_name,
				"dt": "Purchase Order",
				"fieldname": "custom_is_print_item_remarks",
				"label": "是否打印物料备注 (描述)",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": target_after,
				"module": "COS Share",
				"description": "取消勾选后，购销合同类打印格式的明细表不显示「备注」列（不打印物料行描述），以节省版面。",
				"allow_on_submit": 1,
				"print_hide": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache(doctype="Purchase Order")

	if frappe.db.exists("Custom Field", new_name):
		cf = frappe.get_doc("Custom Field", new_name)
		changed = False
		if cf.insert_after != target_after:
			cf.insert_after = target_after
			changed = True
		if cf.label != "是否打印物料备注 (描述)":
			cf.label = "是否打印物料备注 (描述)"
			changed = True
		# 提交后需可改，否则打印始终读到保存时的旧值
		if int(cf.allow_on_submit or 0) != 1:
			cf.allow_on_submit = 1
			changed = True
		if changed:
			cf.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.clear_cache(doctype="Purchase Order")

	if (
		frappe.db.exists("Custom Field", old_name)
		and frappe.db.has_column("Purchase Order", "custom_is_print_item_remarks")
		and frappe.db.has_column("Purchase Order", "custom_print_item_description")
	):
		frappe.db.sql(
			"""
			UPDATE `tabPurchase Order`
			SET `custom_is_print_item_remarks` = IFNULL(`custom_print_item_description`, 1)
			"""
		)
		frappe.db.commit()

		old = frappe.get_doc("Custom Field", old_name)
		if not int(old.hidden or 0):
			old.hidden = 1
			old.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.clear_cache(doctype="Purchase Order")

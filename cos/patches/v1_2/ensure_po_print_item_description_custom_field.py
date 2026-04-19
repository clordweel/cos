# Copyright (c) 2026, COS and contributors
"""确保采购订单存在「打印物料描述」自定义字段（合同打印用）。

说明：若仅依赖 fixtures，部分站点未跑完整 migrate 或 app 未更新时可能缺字段。
字段放在 `custom_hide_contract_seal` 之后，与购销合同打印选项同区，避免落在折叠的「打印设置」里不易发现。
"""

from __future__ import annotations

import frappe


def execute():
	name = "Purchase Order-custom_print_item_description"
	target_after = "custom_hide_contract_seal"

	if frappe.db.exists("Custom Field", name):
		cf = frappe.get_doc("Custom Field", name)
		if cf.insert_after != target_after or not int(cf.allow_on_submit or 0):
			cf.insert_after = target_after
			cf.allow_on_submit = 1
			cf.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.clear_cache(doctype="Purchase Order")
		return

	doc = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"name": name,
			"dt": "Purchase Order",
			"fieldname": "custom_print_item_description",
			"label": "打印物料描述",
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

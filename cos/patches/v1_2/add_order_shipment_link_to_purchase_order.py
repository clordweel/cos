# Copyright (c) 2026, COS and contributors
"""为采购订单 Purchase Order 添加订单运单 Order Shipment 的关联链接，在 Links 区域显示。"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Order Shipment"):
		return
	# 若已存在则跳过
	existing = frappe.db.exists(
		"DocType Link",
		{"parent": "Purchase Order", "link_doctype": "Order Shipment", "link_fieldname": "purchase_order"},
	)
	if existing:
		return
	# 获取最大 idx
	max_idx = frappe.db.sql(
		"SELECT COALESCE(MAX(idx), 0) FROM `tabDocType Link` WHERE parent = 'Purchase Order'"
	)
	idx = (max_idx[0][0] if max_idx else 0) + 1
	link = frappe.get_doc(
		{
			"doctype": "DocType Link",
			"parent": "Purchase Order",
			"parenttype": "DocType",
			"parentfield": "links",
			"idx": idx,
			"link_doctype": "Order Shipment",
			"link_fieldname": "purchase_order",
			"group": "Buying",
			"custom": 1,
		}
	)
	link.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype="Purchase Order")

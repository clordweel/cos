# Copyright (c) 2026, COS and contributors
"""清理 Purchase Order 中重复的 Order Shipment 关联链接，仅保留一条。"""

import frappe


def execute():
	rows = frappe.db.get_all(
		"DocType Link",
		filters={
			"parent": "Purchase Order",
			"link_doctype": "Order Shipment",
			"link_fieldname": "purchase_order",
		},
		fields=["name"],
		order_by="creation asc",
	)
	if len(rows) <= 1:
		return
	# 保留第一条，删除其余
	to_delete = [r.name for r in rows[1:]]
	for name in to_delete:
		frappe.delete_doc("DocType Link", name, ignore_permissions=True, force=True)
	frappe.db.commit()
	frappe.clear_cache(doctype="Purchase Order")

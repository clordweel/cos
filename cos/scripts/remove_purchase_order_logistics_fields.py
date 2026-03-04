# Copyright (c) 2026, COS and contributors
"""
移除采购订单中的物流运单标签及相关自定义字段。
执行: bench --site <site> execute cos.scripts.remove_purchase_order_logistics_fields.remove
"""
import frappe


def remove():
	"""删除 Purchase Order 上物流相关的 Custom Field"""
	keywords = ["物流", "运单", "shipment", "logistics"]
	rows = frappe.get_all(
		"Custom Field",
		filters={"dt": "Purchase Order"},
		fields=["name", "fieldname", "label", "fieldtype", "options"],
	)
	removed = []
	for r in rows:
		label_lower = (r.label or "").lower()
		field_lower = (r.fieldname or "").lower()
		opts_lower = (r.options or "").lower()
		for kw in keywords:
			if kw in label_lower or kw in field_lower or kw in opts_lower:
				frappe.delete_doc("Custom Field", r.name, force=1)
				removed.append(r.name)
				break
	if removed:
		frappe.db.commit()
		print(f"已移除 Custom Field: {', '.join(removed)}")
	else:
		print("未找到需移除的物流相关 Custom Field")

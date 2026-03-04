# Copyright (c) 2026, COS and contributors
"""删除 Order Shipment 数据及表，由 doctype sync 按新 schema（logistics/logistics_name）重建。接受数据丢失。"""

import frappe


def execute():
	# 1. 删除所有 Order Shipment 记录
	if frappe.db.table_exists("Order Shipment"):
		frappe.db.sql("DELETE FROM `tabOrder Shipment`")
		frappe.db.sql("DROP TABLE IF EXISTS `tabOrder Shipment`")

	# 2. Courier Company -> Logistics Company（若存在）
	if frappe.db.table_exists("Courier Company"):
		frappe.rename_doc("DocType", "Courier Company", "Logistics Company", force=True, merge=False)
	# 3. Logistics Company: courier_name -> logistics_name（若存在）
	if frappe.db.table_exists("Logistics Company") and frappe.db.column_exists("Logistics Company", "courier_name"):
		frappe.db.sql(
			"ALTER TABLE `tabLogistics Company` CHANGE COLUMN `courier_name` `logistics_name` VARCHAR(140)"
		)

	frappe.db.commit()

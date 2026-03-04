# Copyright (c) 2026, COS and contributors
"""清理订单物流旧数据与 DocType，便于在干净状态下重新部署。

用法（在 dev/prod 服务器上）:
  bench --site <站点名> execute cos.scripts.clean_order_shipment_for_redeploy.clean

执行后需运行 bench migrate 以按 order_shipment.json 重建 Order Shipment。
"""

from __future__ import annotations

import frappe


def clean(site: str | None = None) -> dict:
	"""删除 Order Shipment 数据、表及 DocType；处理 Courier Company。返回执行结果。"""
	frappe.connect(site=site)
	done = []

	# 1. 删除所有 Order Shipment 记录并删表（DDL 用 sql_ddl 避免 ImplicitCommitError）
	if frappe.db.table_exists("Order Shipment"):
		frappe.db.sql("DELETE FROM `tabOrder Shipment`")
		frappe.db.commit()
		frappe.db.sql_ddl("DROP TABLE IF EXISTS `tabOrder Shipment`")
		done.append("dropped tabOrder Shipment")

	# 2. 删除 Order Shipment DocType 记录（migrate 时从 JSON 重建）
	if frappe.db.exists("DocType", "Order Shipment"):
		frappe.db.sql("DELETE FROM `tabDocField` WHERE parent = 'Order Shipment'")
		frappe.db.sql("DELETE FROM `tabDocPerm` WHERE parent = 'Order Shipment'")
		frappe.db.sql("DELETE FROM `tabDocType` WHERE name = 'Order Shipment'")
		done.append("deleted Order Shipment DocType")

	# 3. Courier Company -> Logistics Company
	if frappe.db.table_exists("Courier Company"):
		frappe.rename_doc("DocType", "Courier Company", "Logistics Company", force=True, merge=False)
		done.append("renamed Courier Company -> Logistics Company")

	# 4. Logistics Company: courier_name -> logistics_name
	if frappe.db.table_exists("Logistics Company") and frappe.db.column_exists("Logistics Company", "courier_name"):
		frappe.db.sql(
			"ALTER TABLE `tabLogistics Company` CHANGE COLUMN `courier_name` `logistics_name` VARCHAR(140)"
		)
		done.append("renamed courier_name -> logistics_name in Logistics Company")

	frappe.db.commit()
	return {"done": done}

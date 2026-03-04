# Copyright (c) 2026, COS and contributors
"""删除 Order Shipment 数据及表，由 doctype sync 按新 schema（logistics/logistics_name）重建。接受数据丢失。"""

import frappe


def _run_ddl(sql: str) -> None:
	"""用独立连接执行 DDL，绕过 Frappe 事务的 ImplicitCommitError。"""
	import pymysql

	conf = frappe.conf
	conn = pymysql.connect(
		host=conf.get("db_host") or "localhost",
		user=conf.get("db_user") or conf.get("db_name") or getattr(frappe.local, "site", "root"),
		password=conf.get("db_password") or "",
		database=conf.get("db_name"),
		autocommit=True,
	)
	try:
		with conn.cursor() as cur:
			cur.execute(sql)
	finally:
		conn.close()


def execute():
	# 1. 删除所有 Order Shipment 记录
	if frappe.db.table_exists("Order Shipment"):
		frappe.db.sql("DELETE FROM `tabOrder Shipment`")
		frappe.db.commit()
		_run_ddl("DROP TABLE IF EXISTS `tabOrder Shipment`")

	# 2. Courier Company -> Logistics Company（若存在）
	if frappe.db.table_exists("Courier Company"):
		frappe.rename_doc("DocType", "Courier Company", "Logistics Company", force=True, merge=False)
	# 3. Logistics Company: courier_name -> logistics_name（若存在）
	if frappe.db.table_exists("Logistics Company") and frappe.db.column_exists("Logistics Company", "courier_name"):
		_run_ddl(
			"ALTER TABLE `tabLogistics Company` CHANGE COLUMN `courier_name` `logistics_name` VARCHAR(140)"
		)

	frappe.db.commit()

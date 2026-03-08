# Copyright (c) 2026, COS and contributors
"""Order Shipment 状态字段拆分：物流状态 -> logistics_status，手动签收 -> status。
pre_model_sync 执行，在 schema 删除 receipt_status 前完成迁移。"""

import frappe


def _run_ddl(sql: str) -> None:
	"""用独立连接执行 DDL。"""
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
	if not frappe.db.table_exists("Order Shipment"):
		return
	# 若已有 logistics_status 且 status 已是 待确认/已签收，说明已迁移
	if frappe.db.column_exists("Order Shipment", "logistics_status"):
		sample = frappe.db.sql(
			"SELECT status FROM `tabOrder Shipment` WHERE status IS NOT NULL LIMIT 1",
			as_dict=1,
		)
		if sample and sample[0].get("status") in ("待确认", "已签收"):
			return
	# 1. 添加 logistics_status 列（若不存在）
	if not frappe.db.column_exists("Order Shipment", "logistics_status"):
		_run_ddl("ALTER TABLE `tabOrder Shipment` ADD COLUMN `logistics_status` VARCHAR(140)")
	# 2. 原 status(物流) -> logistics_status
	frappe.db.sql(
		"UPDATE `tabOrder Shipment` SET logistics_status = status WHERE status IS NOT NULL AND status NOT IN ('待确认', '已签收')"
	)
	# 3. 原 receipt_status -> status（手动签收）
	if frappe.db.column_exists("Order Shipment", "receipt_status"):
		frappe.db.sql(
			"UPDATE `tabOrder Shipment` SET status = COALESCE(receipt_status, '待确认') WHERE receipt_status IS NOT NULL"
		)
	# 4. 仍为物流值的 status 置为待确认
	frappe.db.sql(
		"UPDATE `tabOrder Shipment` SET status = '待确认' WHERE status IS NULL OR status = '' OR status NOT IN ('待确认', '已签收')"
	)
	frappe.db.commit()

# Copyright (c) 2026, COS and contributors
# License: GNU General Public License v3. See license.txt
"""
订单在途报表：展示有运单的采购订单运单，可按物流状态筛选（含已签收）。
"""

import frappe


def execute(filters=None):
	filters = filters or {}
	company = filters.get("company") or ""
	supplier = filters.get("supplier") or ""
	logistics_status = filters.get("logistics_status") or "在途"
	columns = [
		{
			"label": "采购订单",
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 140,
		},
		{
			"label": "供应商",
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120,
		},
		{
			"label": "运单号",
			"fieldname": "tracking_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": "物流公司",
			"fieldname": "logistics_name",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": "运单状态",
			"fieldname": "shipment_status",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "最后查询",
			"fieldname": "last_track_time",
			"fieldtype": "Datetime",
			"width": 140,
		},
	]
	conditions = ["po.docstatus = 1"]
	if company:
		conditions.append("po.company = %(company)s")
	if supplier:
		conditions.append("po.supplier = %(supplier)s")
	# 物流状态：全部=不限制；在途=排除已签收；已签收=仅已签收
	if logistics_status == "在途":
		conditions.append("(s.status IS NULL OR s.status NOT IN ('签收', '已签收'))")
	elif logistics_status == "已签收":
		conditions.append("s.status IN ('签收', '已签收')")
	sql = """
		SELECT s.purchase_order, po.supplier, s.tracking_no, s.logistics_name,
			   s.status AS shipment_status, s.last_track_time
		FROM `tabOrder Shipment` s
		INNER JOIN `tabPurchase Order` po ON po.name = s.purchase_order
		WHERE """ + " AND ".join(conditions)
	data = frappe.db.sql(sql, {"company": company, "supplier": supplier}, as_dict=1)
	return columns, data

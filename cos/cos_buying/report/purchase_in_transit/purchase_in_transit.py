# Copyright (c) 2026, COS and contributors
# License: GNU General Public License v3. See license.txt
"""
采购在途物料报表：展示有运单且状态非「已签收」的采购订单运单。
"""

import frappe


def execute(filters=None):
	filters = filters or {}
	company = filters.get("company") or ""
	supplier = filters.get("supplier") or ""
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
			"label": "快递公司",
			"fieldname": "courier_name",
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
	sql = """
		SELECT s.purchase_order, po.supplier, s.tracking_no, s.courier_name,
			   s.status AS shipment_status, s.last_track_time
		FROM `tabOrder Shipment` s
		INNER JOIN `tabPurchase Order` po ON po.name = s.purchase_order
		WHERE (s.status IS NULL OR s.status NOT IN ('签收', '已签收'))
		  AND """ + " AND ".join(conditions)
	data = frappe.db.sql(sql, {"company": company, "supplier": supplier}, as_dict=1)
	return columns, data

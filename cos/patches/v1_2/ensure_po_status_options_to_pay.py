# Copyright (c) 2026, COS and contributors
"""采购订单 status 补上 To Pay，否则提交后改明细会被 Select 校验拦住。"""

from __future__ import annotations

import frappe

from cos.cos_buying.purchase_order_rate import PO_STATUS_OPTIONS


def execute():
	existing = frappe.db.exists(
		"Property Setter",
		{
			"doc_type": "Purchase Order",
			"field_name": "status",
			"property": "options",
		},
	)
	if existing:
		cur = frappe.db.get_value("Property Setter", existing, "value") or ""
		if "To Pay" in cur.split("\n"):
			return
		frappe.db.set_value("Property Setter", existing, "value", PO_STATUS_OPTIONS)
	else:
		frappe.make_property_setter(
			{
				"doctype": "Purchase Order",
				"doctype_or_field": "DocField",
				"fieldname": "status",
				"property": "options",
				"value": PO_STATUS_OPTIONS,
				"property_type": "Text",
			},
			validate_fields_for_doctype=False,
		)
	frappe.clear_cache(doctype="Purchase Order")

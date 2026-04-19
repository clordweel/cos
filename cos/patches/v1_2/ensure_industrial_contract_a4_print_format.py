# Copyright (c) 2026, COS and contributors
"""确保「采购订单 - 合同 - 工业产品 A4」打印格式存在，并从仓库同步模板。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_contract_po_so_print_formats import sync_one_print_format

	name = "采购订单 - 合同 - 工业产品 A4"
	subdir = "contract-industrial-product-purchase-a4"
	if not frappe.db.exists("Print Format", name):
		doc = frappe.get_doc(
			{
				"doctype": "Print Format",
				"name": name,
				"doc_type": "Purchase Order",
				"module": "COS Share",
				"print_format_type": "Jinja",
				"print_format_for": "DocType",
				"custom_format": 1,
				"default_print_language": "zh",
				"disabled": 0,
				"pdf_generator": "chrome",
				"page_number": "Hide",
				"html": "<div></div>",
				"css": "",
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

	try:
		sync_one_print_format(name, subdir)
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: industrial A4 contract",
			message=str(e),
		)
	frappe.db.commit()

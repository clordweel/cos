# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""COS Work Mini Program / Role：补全 Fixture 导出模块键（与 hooks fixtures 筛选一致）。"""

import frappe


def execute():
	if frappe.db.has_column("tabCOS Work Mini Program", "export_module"):
		frappe.db.sql(
			"""
			UPDATE `tabCOS Work Mini Program`
			SET export_module = %s
			WHERE ifnull(export_module, '') = ''
			""",
			("COS Share",),
		)
	if frappe.db.has_column("tabCOS Work Mini Program Role", "export_module"):
		frappe.db.sql(
			"""
			UPDATE `tabCOS Work Mini Program Role`
			SET export_module = %s
			WHERE ifnull(export_module, '') = ''
			""",
			("COS Share",),
		)

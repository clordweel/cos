"""将 custom_employee_reimbursed 列从 int 改为 varchar，以支持 Select 类型。"""
from __future__ import annotations

import frappe


def execute():
	# 先更新 Custom Field doc，再 ALTER 列（fixture 可能未在 migrate 时重载）
	cf = frappe.db.get_value(
		"Custom Field",
		{"dt": "Purchase Invoice", "fieldname": "custom_employee_reimbursed"},
		"name",
	)
	if not cf:
		return
	doc = frappe.get_doc("Custom Field", cf)
	doc.fieldtype = "Select"
	doc.options = "未报销\n已报销"
	doc.default = "未报销"
	doc.label = "员工报销状态"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	# 显式 ALTER 列（应对 schema sync 未及时更新）
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` MODIFY COLUMN `custom_employee_reimbursed` VARCHAR(140)"
	)
	frappe.db.commit()

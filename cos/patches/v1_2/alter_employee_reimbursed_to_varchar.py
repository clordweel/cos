"""将 custom_employee_reimbursed 列从 int 改为 varchar，以支持 Select 类型。"""
from __future__ import annotations

import frappe


def execute():
	cf = frappe.db.get_value(
		"Custom Field",
		{"dt": "Purchase Invoice", "fieldname": "custom_employee_reimbursed"},
		"name",
	)
	if not cf:
		return
	# 1) 先 ALTER 列（避免 doc.save 触发 updatedb 时列仍为 int）
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` MODIFY COLUMN `custom_employee_reimbursed` VARCHAR(140)"
	)
	frappe.db.commit()
	# 2) 再更新 Custom Field doc（fixture 可能未在 migrate 时重载）
	doc = frappe.get_doc("Custom Field", cf)
	doc.fieldtype = "Select"
	doc.options = "未报销\n已报销"
	doc.default = "未报销"
	doc.label = "员工报销状态"
	doc.flags.ignore_validate = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()

"""强制将 custom_employee_reimbursed 的 Custom Field doc 更新为 Select 类型，确保 UI 显示下拉选择。"""
from __future__ import annotations

import frappe


def execute():
	name = frappe.db.get_value(
		"Custom Field",
		{"dt": "Purchase Invoice", "fieldname": "custom_employee_reimbursed"},
		"name",
	)
	if not name:
		return
	doc = frappe.get_doc("Custom Field", name)
	doc.fieldtype = "Select"
	doc.label = "员工报销状态"
	doc.options = "未报销\n已报销"
	doc.default = "未报销"
	doc.description = "付给员工 PE 提交后由系统自动更新为「已报销」；用于筛选「员工垫付未报销」"
	doc.flags.ignore_validate = True
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()

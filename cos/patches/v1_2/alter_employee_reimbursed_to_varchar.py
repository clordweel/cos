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
	# 通过临时列转换，避免 MODIFY 时 MySQL 对默认值/转换的严格校验
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` ADD COLUMN `_custom_employee_reimbursed_tmp` VARCHAR(140)"
	)
	frappe.db.sql(
		"UPDATE `tabPurchase Invoice` SET `_custom_employee_reimbursed_tmp` = "
		"CASE WHEN COALESCE(`custom_employee_reimbursed`, 0) = 1 THEN '已报销' ELSE '未报销' END"
	)
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` DROP COLUMN `custom_employee_reimbursed`"
	)
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` CHANGE COLUMN `_custom_employee_reimbursed_tmp` "
	"`custom_employee_reimbursed` VARCHAR(140)"
	)
	frappe.db.commit()

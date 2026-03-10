"""将 custom_employee_reimbursed 列从 int 改为 varchar，以支持 Select 类型。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.get_meta("Purchase Invoice").has_field("custom_employee_reimbursed"):
		return
	# Check 字段为 tinyint，Select 需 varchar
	frappe.db.sql(
		"ALTER TABLE `tabPurchase Invoice` MODIFY COLUMN `custom_employee_reimbursed` VARCHAR(140)"
	)
	frappe.db.commit()

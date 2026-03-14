"""移除旧的 custom_advance_employee_editable_users 字段，已改为基于角色的 custom_advance_employee_editable_role。"""
from __future__ import annotations

import frappe


def execute():
	name = "Buying Settings-custom_advance_employee_editable_users"
	if frappe.db.exists("Custom Field", name):
		frappe.delete_doc("Custom Field", name, force=True)
		frappe.db.commit()

"""创建 Biometric Manager 角色（供考勤机 DocType 权限引用）。"""
from __future__ import annotations

import frappe


def execute():
	if frappe.db.exists("Role", "Biometric Manager"):
		return
	doc = frappe.new_doc("Role")
	doc.name = "Biometric Manager"
	doc.desk_access = 1
	doc.insert(ignore_permissions=True)

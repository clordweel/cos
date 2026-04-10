"""若不存在则插入 Biometric Sync Settings 默认单例。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Biometric Sync Settings"):
		return
	# migrate 过程中可能出现 tabDocType 已有记录但物理表尚未创建的情况，避免 get_all 报错
	if not frappe.db.has_table("Biometric Sync Settings"):
		raise RuntimeError(
			"Biometric Sync Settings 表尚未创建；请再次执行 bench migrate 以完成 schema 后再跑本 patch。"
		)
	if frappe.db.get_all("Biometric Sync Settings", limit=1):
		return
	doc = frappe.new_doc("Biometric Sync Settings")
	doc.systemd_service_name = "cos-biometric-sync.service"
	doc.hrms_employee_fieldname = "attendance_device_id"
	doc.insert(ignore_permissions=True)

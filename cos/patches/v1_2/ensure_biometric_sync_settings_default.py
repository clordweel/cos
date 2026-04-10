"""若不存在则插入 Biometric Sync Settings 默认单例。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Biometric Sync Settings"):
		return
	if frappe.db.get_all("Biometric Sync Settings", limit=1):
		return
	doc = frappe.new_doc("Biometric Sync Settings")
	doc.systemd_service_name = "cos-biometric-sync.service"
	doc.hrms_employee_fieldname = "attendance_device_id"
	doc.insert(ignore_permissions=True)

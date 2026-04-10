"""若不存在则插入 Biometric Sync Settings 默认单例。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Biometric Sync Settings"):
		return
	# issingle=1：数据在 tabSingles，勿用 get_all（会误查不存在的 tabBiometric Sync Settings）
	if frappe.db.exists("Biometric Sync Settings", "Biometric Sync Settings"):
		return
	doc = frappe.new_doc("Biometric Sync Settings")
	doc.systemd_service_name = "cos-biometric-sync.service"
	doc.hrms_employee_fieldname = "attendance_device_id"
	doc.insert(ignore_permissions=True)

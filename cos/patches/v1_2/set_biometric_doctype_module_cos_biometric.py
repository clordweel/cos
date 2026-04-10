"""考勤相关 DocType 的 module 统一为 COS Biometric（与 cos_biometric 包一致）。"""
from __future__ import annotations

import frappe

TARGETS = (
	"Biometric Device",
	"Biometric Sync Settings",
	"Biometric Device Action Log",
)


def execute() -> None:
	for name in TARGETS:
		if not frappe.db.exists("DocType", name):
			continue
		frappe.db.set_value("DocType", name, "module", "COS Biometric")

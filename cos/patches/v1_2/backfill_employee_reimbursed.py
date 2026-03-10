"""回填 PI 的 custom_employee_reimbursed（员工已报销）字段。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.get_meta("Purchase Invoice").has_field("custom_employee_reimbursed"):
		return
	from cos.scripts.backfill_employee_reimbursed import run

	run()

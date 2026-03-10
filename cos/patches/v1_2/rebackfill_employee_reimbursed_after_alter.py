"""alter 后将 custom_employee_reimbursed 重新回填为「未报销」/「已报销」。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.get_meta("Purchase Invoice").has_field("custom_employee_reimbursed"):
		return
	from cos.scripts.backfill_employee_reimbursed import run

	run()

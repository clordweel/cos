"""再次回填 custom_employee_reimbursed（改为 Select 后需重新计算，并迁移旧 0/1 值）。"""
from __future__ import annotations

import frappe


def execute():
	if not frappe.get_meta("Purchase Invoice").has_field("custom_employee_reimbursed"):
		return
	from cos.scripts.backfill_employee_reimbursed import run

	run()

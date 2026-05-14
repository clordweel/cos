# Copyright (c) 2026, COS and contributors
"""上线 Employee Advance 工作流后，可对齐存量草稿单的 workflow_state。"""

from __future__ import annotations

import frappe
from frappe.query_builder import DocType

INITIAL_STATE = "COS EA Draft"


def sync_draft_employee_advances_to_initial_state():
	"""将 docstatus=0 且 workflow_state 为空的员工预支单设为 ``COS EA Draft``（须 System Manager）。

	bench --site <站点> execute cos.cos_accounts.utils.employee_advance_workflow_sync.sync_draft_employee_advances_to_initial_state
	"""
	frappe.only_for("System Manager")
	ea = DocType("Employee Advance")
	q = (
		frappe.qb.from_(ea)
		.select(ea.name)
		.where((ea.docstatus == 0) & ((ea.workflow_state.isnull()) | (ea.workflow_state == "")))
	)
	names = [r[0] for r in q.run()]
	for name in names:
		frappe.db.set_value(
			"Employee Advance",
			name,
			"workflow_state",
			INITIAL_STATE,
			update_modified=False,
		)
	frappe.db.commit()
	return len(names)

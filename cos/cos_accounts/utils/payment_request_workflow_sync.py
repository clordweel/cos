# Copyright (c) 2026, COS and contributors
"""上线 Payment Request 工作流后，对齐存量未提交单据的 workflow_state。"""

from __future__ import annotations

import frappe
from frappe.query_builder import DocType

INITIAL_STATE = "COS PR Draft"


def sync_draft_payment_requests_to_initial_state():
	"""将 docstatus=0 且 workflow_state 为空的 PR 设为 COS PR Draft（须 System Manager）。

	bench --site <站点> execute cos.cos_accounts.utils.payment_request_workflow_sync.sync_draft_payment_requests_to_initial_state
	"""
	frappe.only_for("System Manager")
	pr = DocType("Payment Request")
	q = (
		frappe.qb.from_(pr)
		.select(pr.name)
		.where((pr.docstatus == 0) & ((pr.workflow_state.isnull()) | (pr.workflow_state == "")))
	)
	names = [r[0] for r in q.run()]
	for name in names:
		frappe.db.set_value(
			"Payment Request",
			name,
			"workflow_state",
			INITIAL_STATE,
			update_modified=False,
		)
	frappe.db.commit()
	return len(names)

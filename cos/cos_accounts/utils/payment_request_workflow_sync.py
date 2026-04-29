# Copyright (c) 2026, COS and contributors
"""上线 Payment Request 工作流后，对齐存量单据 workflow_state。"""

from __future__ import annotations

import frappe
from frappe.query_builder import DocType

INITIAL_STATE = "COS PR Draft"
_LEGACY_TO_NEW_STATE = {
	"": INITIAL_STATE,
	"Draft": INITIAL_STATE,
	"草稿": INITIAL_STATE,
	"Pending Applicant": "COS PR Pending Applicant",
	"待申请人确认": "COS PR Pending Applicant",
	"Pending Finance": "COS PR Pending Finance",
	"待财务审核": "COS PR Pending Finance",
	"Pending Director": "COS PR Pending Director",
	"待老板批准": "COS PR Pending Director",
	"Approved": "COS PR Approved",
	"已批准可提交": "COS PR Approved",
}
_VALID_STATES = set(
	[
		"COS PR Draft",
		"COS PR Pending Applicant",
		"COS PR Pending Finance",
		"COS PR Pending Director",
		"COS PR Approved",
		"COS PR Cancelled",
	]
)


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


def sync_cancelled_payment_requests_workflow_state():
	"""将已取消（docstatus=2）且仍未写入终审取消状态的 PR 统一设为 COS PR Cancelled（须 System Manager）。

	适用于上线本钩子前的存量单据；新开单据由 ``payment_request_on_cancel`` 自动写入。

	bench --site <站点> execute cos.cos_accounts.utils.payment_request_workflow_sync.sync_cancelled_payment_requests_workflow_state
	"""
	frappe.only_for("System Manager")
	if not frappe.db.exists("Workflow", "COS Payment Request Approval"):
		return 0
	cancelled = "COS PR Cancelled"
	pr = DocType("Payment Request")
	q = (
		frappe.qb.from_(pr)
		.select(pr.name)
		.where((pr.docstatus == 2) & (pr.workflow_state != cancelled))
	)
	names = [r[0] for r in q.run()]
	for name in names:
		frappe.db.set_value(
			"Payment Request",
			name,
			"workflow_state",
			cancelled,
			update_modified=False,
		)
	if names:
		frappe.db.commit()
	return len(names)


def normalize_payment_request_workflow_state_values():
	"""对齐旧状态值，避免前端因 state 不匹配被判定为只读。"""
	pr = DocType("Payment Request")
	rows = (
		frappe.qb.from_(pr)
		.select(pr.name, pr.docstatus, pr.workflow_state)
		.where(pr.docstatus == 0)
	).run(as_dict=True)
	updated = 0
	for row in rows:
		cur = (row.workflow_state or "").strip()
		if cur in _VALID_STATES:
			continue
		target = _LEGACY_TO_NEW_STATE.get(cur, INITIAL_STATE)
		if cur == target:
			continue
		frappe.db.set_value(
			"Payment Request",
			row.name,
			"workflow_state",
			target,
			update_modified=False,
		)
		updated += 1
	if updated:
		frappe.db.commit()
	return updated

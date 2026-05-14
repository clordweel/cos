# Copyright (c) 2026, COS and contributors
"""标准 Employee Advance（员工预支 / 备用金）：三级工作流与收付款申请（Payment Request）同构。

角色：All（业务确认阶段） / Accounts User（财务） / Expense Approver（终审）。
终态 ``COS EA Approved`` 保存后由 ``employee_advance_on_update`` 自动 Submit（同 PR/EAPR）。
"""

from __future__ import annotations

import frappe
from frappe import _

WORKFLOW_DOC_NAME = "COS Employee Advance Approval"
FINAL_STATE = "COS EA Approved"
STATE_PENDING_FINANCE = "COS EA Pending Finance"
STATE_PENDING_DIRECTOR = "COS EA Pending Director"
STATE_APPROVED = "COS EA Approved"
STATE_CANCELLED = "COS EA Cancelled"
INITIAL_STATE = "COS EA Draft"

WORKFLOW_STATE_ORDER = (
	"COS EA Draft",
	"COS EA Pending Applicant",
	"COS EA Pending Finance",
	"COS EA Pending Director",
	STATE_APPROVED,
)


def _workflow_state_index(state: str | None) -> int:
	if state in WORKFLOW_STATE_ORDER:
		return WORKFLOW_STATE_ORDER.index(state)
	return -1


def _clear_ea_approval_trail_on_reject(doc, new_wf: str) -> None:
	if new_wf == "COS EA Draft":
		for f in (
			"custom_eadv_applicant_confirmed_by",
			"custom_eadv_applicant_confirmed_on",
			"custom_eadv_finance_approved_by",
			"custom_eadv_finance_approved_on",
			"custom_eadv_boss_approved_by",
			"custom_eadv_boss_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS EA Pending Applicant":
		for f in (
			"custom_eadv_applicant_confirmed_by",
			"custom_eadv_applicant_confirmed_on",
			"custom_eadv_finance_approved_by",
			"custom_eadv_finance_approved_on",
			"custom_eadv_boss_approved_by",
			"custom_eadv_boss_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS EA Pending Finance":
		doc.set("custom_eadv_boss_approved_by", None)
		doc.set("custom_eadv_boss_approved_on", None)


def _clear_all_ea_trail(doc) -> None:
	for f in (
		"custom_eadv_applicant_confirmed_by",
		"custom_eadv_applicant_confirmed_on",
		"custom_eadv_finance_approved_by",
		"custom_eadv_finance_approved_on",
		"custom_eadv_boss_approved_by",
		"custom_eadv_boss_approved_on",
	):
		doc.set(f, None)


def _reset_amended_employee_advance_to_draft(doc) -> bool:
	if not doc.is_new() or not doc.get("amended_from"):
		return False
	doc.set("workflow_state", INITIAL_STATE)
	_clear_all_ea_trail(doc)
	return True


def employee_advance_before_validate(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_employee_advance_to_draft(doc)


def employee_advance_validate(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_employee_advance_to_draft(doc)


def get_final_workflow_state_for_employee_advance():
	if not frappe.db.get_value(
		"Workflow",
		{"document_type": "Employee Advance", "is_active": 1},
		"name",
	):
		return None
	if frappe.db.exists("Workflow", WORKFLOW_DOC_NAME):
		return FINAL_STATE
	return FINAL_STATE


def employee_advance_before_submit(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	final = get_final_workflow_state_for_employee_advance()
	if final is None:
		return
	if doc.get("workflow_state") != final:
		cur = doc.get("workflow_state")
		frappe.throw(
			_(
				"Employee Advance cannot be submitted until workflow reaches {0}. Current state: {1}"
			).format(
				_(final),
				_(cur) if cur else _("Not set"),
			)
		)


def employee_advance_on_update(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if getattr(frappe.local, "_cos_ea_auto_submit_in_progress", False):
		return
	if doc.docstatus != 0:
		return
	final = get_final_workflow_state_for_employee_advance()
	if final is None:
		return
	if doc.get("workflow_state") != final:
		return
	frappe.local._cos_ea_auto_submit_in_progress = True
	try:
		doc.reload()
		if doc.docstatus != 0 or doc.get("workflow_state") != final:
			return
		doc.submit()
	finally:
		frappe.local._cos_ea_auto_submit_in_progress = False


def employee_advance_before_save(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if _reset_amended_employee_advance_to_draft(doc):
		return
	if doc.is_new():
		return
	prev_wf = frappe.db.get_value("Employee Advance", doc.name, "workflow_state")
	new_wf = doc.get("workflow_state")
	if prev_wf == new_wf:
		return
	i_prev, i_new = _workflow_state_index(prev_wf), _workflow_state_index(new_wf)
	if i_prev >= 0 and i_new >= 0 and i_new < i_prev:
		_clear_ea_approval_trail_on_reject(doc, new_wf)
		return
	user = frappe.session.user
	now = frappe.utils.now()
	if new_wf == STATE_PENDING_FINANCE:
		doc.set("custom_eadv_applicant_confirmed_by", user)
		doc.set("custom_eadv_applicant_confirmed_on", now)
	elif new_wf == STATE_PENDING_DIRECTOR:
		doc.set("custom_eadv_finance_approved_by", user)
		doc.set("custom_eadv_finance_approved_on", now)
	elif new_wf == STATE_APPROVED:
		doc.set("custom_eadv_boss_approved_by", user)
		doc.set("custom_eadv_boss_approved_on", now)


def employee_advance_on_cancel(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	wname = frappe.db.get_value(
		"Workflow",
		{"document_type": "Employee Advance", "is_active": 1},
		"name",
	)
	if wname != WORKFLOW_DOC_NAME:
		return
	frappe.db.set_value(
		"Employee Advance",
		doc.name,
		"workflow_state",
		STATE_CANCELLED,
		update_modified=False,
	)
	doc.set("workflow_state", STATE_CANCELLED)

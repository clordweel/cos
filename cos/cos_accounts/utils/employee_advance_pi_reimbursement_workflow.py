# Copyright (c) 2026, COS and contributors
"""Employee Advance PI Reimbursement（员工垫付采购报销）：三级工作流并联 PI，终态自动提交后触发应付转员工 JE。

与 ``COS Payment Request Approval`` 同级角色模型：All / Accounts User / Expense Approver。
"""

from __future__ import annotations

import frappe
from frappe import _

WORKFLOW_DOC_NAME = "COS Employee Advance PI Reimbursement Approval"
EAPR_FINAL_STATE = "COS EAPR Approved"
STATE_PENDING_FINANCE = "COS EAPR Pending Finance"
STATE_PENDING_DIRECTOR = "COS EAPR Pending Director"
STATE_APPROVED = "COS EAPR Approved"
STATE_CANCELLED = "COS EAPR Cancelled"
INITIAL_STATE = "COS EAPR Draft"

WORKFLOW_STATE_ORDER = (
	"COS EAPR Draft",
	"COS EAPR Pending Applicant",
	"COS EAPR Pending Finance",
	"COS EAPR Pending Director",
	STATE_APPROVED,
)

_DOCTYPE = "Employee Advance PI Reimbursement"


def _workflow_state_index(state: str | None) -> int:
	if state in WORKFLOW_STATE_ORDER:
		return WORKFLOW_STATE_ORDER.index(state)
	return -1


def _clear_eapr_approval_trail_on_reject(doc, new_wf: str) -> None:
	if new_wf == "COS EAPR Draft":
		for f in (
			"custom_eapr_applicant_confirmed_by",
			"custom_eapr_applicant_confirmed_on",
			"custom_eapr_finance_approved_by",
			"custom_eapr_finance_approved_on",
			"custom_eapr_director_approved_by",
			"custom_eapr_director_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS EAPR Pending Applicant":
		for f in (
			"custom_eapr_applicant_confirmed_by",
			"custom_eapr_applicant_confirmed_on",
			"custom_eapr_finance_approved_by",
			"custom_eapr_finance_approved_on",
			"custom_eapr_director_approved_by",
			"custom_eapr_director_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS EAPR Pending Finance":
		doc.set("custom_eapr_director_approved_by", None)
		doc.set("custom_eapr_director_approved_on", None)


def _clear_all_eapr_trail(doc) -> None:
	for f in (
		"custom_eapr_applicant_confirmed_by",
		"custom_eapr_applicant_confirmed_on",
		"custom_eapr_finance_approved_by",
		"custom_eapr_finance_approved_on",
		"custom_eapr_director_approved_by",
		"custom_eapr_director_approved_on",
	):
		doc.set(f, None)


def _reset_amended_doc_to_draft(doc) -> bool:
	if not doc.is_new() or not doc.get("amended_from"):
		return False
	doc.set("workflow_state", INITIAL_STATE)
	_clear_all_eapr_trail(doc)
	return True


def _active_workflow_name() -> str | None:
	return frappe.db.get_value(
		"Workflow",
		{"document_type": _DOCTYPE, "is_active": 1},
		"name",
	)


def eapr_validate_duplicate_and_pi(doc) -> None:
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return

	if not doc.get("purchase_invoice"):
		return

	pi = frappe.db.get_value(
		"Purchase Invoice",
		doc.purchase_invoice,
		[
			"docstatus",
			"company",
			"name",
			"custom_is_employee_advance",
			"custom_advance_employee",
			"custom_reimbursement_approval_status",
			"custom_payable_transfer_je",
		],
		as_dict=True,
	)
	if not pi:
		frappe.throw(_("请选择有效的采购发票"), title=_("校验失败"))

	if pi.docstatus != 1:
		frappe.throw(_("采购发票须已提交"), title=_("校验失败"))

	if not pi.custom_is_employee_advance:
		frappe.throw(_("仅支持已勾选员工垫付的采购发票"), title=_("校验失败"))

	if not pi.custom_advance_employee:
		frappe.throw(_("请在采购发票上指定垫付员工"), title=_("校验失败"))

	if doc.get("company") and pi.company and doc.company != pi.company:
		frappe.throw(_("公司与采购发票不一致"), title=_("校验失败"))

	if (
		pi.custom_reimbursement_approval_status == "Approved"
		and pi.custom_payable_transfer_je
		and doc.is_new()
	):
		frappe.throw(
			_("该采购发票已完成报销审批且已生成应付转员工凭证，不可重复创建"),
			title=_("重复申请"),
		)

	others = frappe.get_all(
		_DOCTYPE,
		filters={
			"purchase_invoice": doc.purchase_invoice,
			"docstatus": ["in", [0, 1]],
			"name": ["!=", doc.name or ""],
		},
		pluck="name",
	)
	if others:
		frappe.throw(
			_("采购发票 {0} 已存在未取消的报销单：{1}").format(
				doc.purchase_invoice,
				", ".join(others[:5]),
			),
			title=_("重复申请"),
		)


def purchase_invoice_guard_cancel_if_eapr_submitted(doc, method=None):
	"""已存在已提交的报销并联单时，禁止直接取消采购发票（需先取消报销单）。"""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if doc.doctype != "Purchase Invoice" or not doc.name:
		return
	names = frappe.get_all(
		_DOCTYPE,
		filters={"purchase_invoice": doc.name, "docstatus": 1},
		pluck="name",
		limit=1,
	)
	if names:
		frappe.throw(
			_("存在已提交的员工垫付采购报销单 {0}，请先取消报销单再取消采购发票").format(
				frappe.utils.get_link_to_form(_DOCTYPE, names[0])
			),
			title=_("无法取消采购发票"),
		)


def eapr_before_validate(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_doc_to_draft(doc)


def eapr_validate(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_doc_to_draft(doc)


def eapr_before_save(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if _reset_amended_doc_to_draft(doc):
		return
	if doc.is_new():
		return
	prev_wf = frappe.db.get_value(_DOCTYPE, doc.name, "workflow_state")
	new_wf = doc.get("workflow_state")
	if prev_wf == new_wf:
		return
	i_prev, i_new = _workflow_state_index(prev_wf), _workflow_state_index(new_wf)
	if i_prev >= 0 and i_new >= 0 and i_new < i_prev:
		_clear_eapr_approval_trail_on_reject(doc, new_wf)
		pi_name = doc.get("purchase_invoice")
		if pi_name:
			je = frappe.db.get_value("Purchase Invoice", pi_name, "custom_payable_transfer_je")
			if not je:
				frappe.db.set_value(
					"Purchase Invoice",
					pi_name,
					"custom_reimbursement_approval_status",
					"Rejected",
					update_modified=True,
				)
		return
	user = frappe.session.user
	now = frappe.utils.now()
	if new_wf == STATE_PENDING_FINANCE:
		doc.set("custom_eapr_applicant_confirmed_by", user)
		doc.set("custom_eapr_applicant_confirmed_on", now)
	elif new_wf == STATE_PENDING_DIRECTOR:
		doc.set("custom_eapr_finance_approved_by", user)
		doc.set("custom_eapr_finance_approved_on", now)
	elif new_wf == STATE_APPROVED:
		doc.set("custom_eapr_director_approved_by", user)
		doc.set("custom_eapr_director_approved_on", now)


def eapr_before_submit(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	wf = _active_workflow_name()
	if not wf or wf != WORKFLOW_DOC_NAME:
		return
	if doc.get("workflow_state") != EAPR_FINAL_STATE:
		cur = doc.get("workflow_state")
		frappe.throw(
			_("报销单须在工作流到达 {0} 后才可提交。当前：{1}").format(
				_(EAPR_FINAL_STATE),
				_(cur) if cur else _("未设置"),
			)
		)


def eapr_on_update(doc, method=None):
	"""终审保存后自动提交（与 Payment Request 相同 UX）。"""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if getattr(frappe.local, "_cos_eapr_auto_submit_in_progress", False):
		return
	if doc.docstatus != 0:
		return
	wf = _active_workflow_name()
	if not wf or wf != WORKFLOW_DOC_NAME:
		return
	if doc.get("workflow_state") != EAPR_FINAL_STATE:
		return
	frappe.local._cos_eapr_auto_submit_in_progress = True
	try:
		doc.reload()
		if doc.docstatus != 0 or doc.get("workflow_state") != EAPR_FINAL_STATE:
			return
		doc.submit()
	finally:
		frappe.local._cos_eapr_auto_submit_in_progress = False


def eapr_on_cancel(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if not frappe.db.exists("Workflow", WORKFLOW_DOC_NAME):
		return
	frappe.db.set_value(
		_DOCTYPE,
		doc.name,
		"workflow_state",
		STATE_CANCELLED,
		update_modified=False,
	)
	doc.set("workflow_state", STATE_CANCELLED)

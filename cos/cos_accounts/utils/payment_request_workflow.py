# Copyright (c) 2026, COS and contributors
"""Payment Request：三级工作流门禁与审批人/时间回写（与 fixture Workflow 名称一致）。

工作流角色使用 ERPNext 标准角色（须分配给用户，且须具备 Payment Request 权限）：

- 草稿 / 待业务确认：`allow_edit` 与对应 transition 为 **All**（见 workflow fixture）
- **Accounts User**（会计）：待财务阶段可编辑；可「财务核准」或「退回业务确认」
- **Expense Approver**（费用审批人）：待终审阶段可编辑；可「终审核准」或「退回财务复核」
- **已批准可提交**：`allow_edit` 为 **All**（与草稿阶段一致），经办可 **Submit**；实际制证仍受 Payment Entry 等权限约束

驳回：见 ``COS PR Applicant Reject`` / ``COS PR Finance Reject`` / ``COS PR Director Reject``，
回落节点时由 ``payment_request_before_save`` 清理下游审批留痕字段。

上线验证（dev→prod 按 migration 规范）：

1. migrate 后抽样新建 PR：Draft → 工作流至 COS PR Approved，中间不可 Submit。
2. Approved 后可 Submit；打印「收付款申请 - 标准」签字区显示确认人/时间。
3. 存量未提交单：可 bench execute
   ``cos.cos_accounts.utils.payment_request_workflow_sync.sync_draft_payment_requests_to_initial_state``。

「COS PR Approved」状态须 **可编辑**，否则 Desk 整单只读、看不到 **提交** 与「创建收付款凭证」等后续按钮。
当前 fixture 对该状态使用 **All**，与前几步门禁无关：`before_submit` 仍要求 `workflow_state == COS PR Approved`。
"""

from __future__ import annotations

import frappe
from frappe import _

WORKFLOW_DOC_NAME = "COS Payment Request Approval"
FINAL_STATE = "COS PR Approved"
STATE_PENDING_FINANCE = "COS PR Pending Finance"
STATE_PENDING_DIRECTOR = "COS PR Pending Director"
STATE_APPROVED = "COS PR Approved"

WORKFLOW_STATE_ORDER = (
	"COS PR Draft",
	"COS PR Pending Applicant",
	"COS PR Pending Finance",
	"COS PR Pending Director",
	STATE_APPROVED,
)


def _workflow_state_index(state: str | None) -> int:
	if state in WORKFLOW_STATE_ORDER:
		return WORKFLOW_STATE_ORDER.index(state)
	return -1


def _clear_pr_approval_trail_on_reject(doc, new_wf: str) -> None:
	"""驳回后按回落节点清理下游留痕，避免打印与界面仍显示已过审。"""
	if new_wf == "COS PR Draft":
		for f in (
			"custom_pr_applicant_confirmed_by",
			"custom_pr_applicant_confirmed_on",
			"custom_pr_finance_approved_by",
			"custom_pr_finance_approved_on",
			"custom_pr_boss_approved_by",
			"custom_pr_boss_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS PR Pending Applicant":
		for f in (
			"custom_pr_applicant_confirmed_by",
			"custom_pr_applicant_confirmed_on",
			"custom_pr_finance_approved_by",
			"custom_pr_finance_approved_on",
			"custom_pr_boss_approved_by",
			"custom_pr_boss_approved_on",
		):
			doc.set(f, None)
	elif new_wf == "COS PR Pending Finance":
		doc.set("custom_pr_boss_approved_by", None)
		doc.set("custom_pr_boss_approved_on", None)


def get_final_workflow_state_for_payment_request():
	"""若站点存在针对 Payment Request 的活动工作流，则返回终审状态名，否则 None（不拦截提交）。"""
	if not frappe.db.get_value(
		"Workflow",
		{"document_type": "Payment Request", "is_active": 1},
		"name",
	):
		return None
	# 与 cos/fixtures/workflow.json 中终审节点一致
	if frappe.db.exists("Workflow", WORKFLOW_DOC_NAME):
		return FINAL_STATE
	return FINAL_STATE


def payment_request_before_submit(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	final = get_final_workflow_state_for_payment_request()
	if final is None:
		return
	if doc.get("workflow_state") != final:
		cur = doc.get("workflow_state")
		frappe.throw(
			_(
				"Payment Request cannot be submitted until workflow reaches {0}. Current state: {1}"
			).format(
				_(final),
				_(cur) if cur else _("Not set"),
			)
		)


def payment_request_before_save(doc, method=None):
	"""工作流状态变化时写入对应审批人、时间；驳回时清理下游留痕。"""
	if doc.is_new():
		return
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	prev_wf = frappe.db.get_value("Payment Request", doc.name, "workflow_state")
	new_wf = doc.get("workflow_state")
	if prev_wf == new_wf:
		return
	i_prev, i_new = _workflow_state_index(prev_wf), _workflow_state_index(new_wf)
	if i_prev >= 0 and i_new >= 0 and i_new < i_prev:
		_clear_pr_approval_trail_on_reject(doc, new_wf)
		return
	user = frappe.session.user
	now = frappe.utils.now()
	if new_wf == STATE_PENDING_FINANCE:
		doc.set("custom_pr_applicant_confirmed_by", user)
		doc.set("custom_pr_applicant_confirmed_on", now)
	elif new_wf == STATE_PENDING_DIRECTOR:
		doc.set("custom_pr_finance_approved_by", user)
		doc.set("custom_pr_finance_approved_on", now)
	elif new_wf == STATE_APPROVED:
		doc.set("custom_pr_boss_approved_by", user)
		doc.set("custom_pr_boss_approved_on", now)

# Copyright (c) 2026, COS and contributors
"""Payment Request：三级工作流门禁与审批人/时间回写（与 fixture Workflow 名称一致）。

工作流角色使用 ERPNext 标准角色（须分配给用户，且须具备 Payment Request 权限）：

- 草稿 / 待申请人确认：`allow_edit` 与对应 transition 为 **All**（见 workflow fixture）
- **Accounts User**（会计）：待财务审核阶段可编辑；可执行「财务审核」
- **Expense Approver**（费用审批人）：待老板批准阶段可编辑；可执行「老板批准」
- **Purchase User**（采购员）：**已批准可提交**阶段可编辑并提交 ERPNext 单据

上线验证（dev→prod 按 migration 规范）：

1. migrate 后抽样新建 PR：Draft → 四级工作流至 COS PR Approved，中间不可 Submit。
2. Approved 后可 Submit；打印「收付款申请 - 标准」签字区显示确认人/时间。
3. 存量未提交单：可 bench execute
   ``cos.cos_accounts.utils.payment_request_workflow_sync.sync_draft_payment_requests_to_initial_state``。

「COS PR Approved」状态的 allow_edit 须为 **Purchase User**，否则经办在 Desk 上可能整单只读、无提交按钮。
财务/老板需代提交时，应为其勾选 **Purchase User**（或调整工作流 allow_edit）。
"""

from __future__ import annotations

import frappe
from frappe import _

WORKFLOW_DOC_NAME = "COS Payment Request Approval"
FINAL_STATE = "COS PR Approved"
STATE_PENDING_FINANCE = "COS PR Pending Finance"
STATE_PENDING_DIRECTOR = "COS PR Pending Director"
STATE_APPROVED = "COS PR Approved"


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
	"""工作流状态变化时写入对应审批人、时间（与 Transition 结果一致）。"""
	if doc.is_new():
		return
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	prev_wf = frappe.db.get_value("Payment Request", doc.name, "workflow_state")
	new_wf = doc.get("workflow_state")
	if prev_wf == new_wf:
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

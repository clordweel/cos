# Copyright (c) 2026, COS and contributors
"""Payment Request：三级工作流门禁与审批人/时间回写（与 fixture Workflow 名称一致）。

工作流角色使用 ERPNext 标准角色（须分配给用户，且须具备 Payment Request 权限）：

- 草稿 / 待业务确认：`allow_edit` 与对应 transition 为 **All**（见 workflow fixture）
- **Accounts User**（会计）：待财务阶段可编辑；可「财务核准」或「退回业务确认」
- **Expense Approver**（费用审批人）：待终审阶段可编辑；可「终审核准」或「退回财务复核」
- **已批准**（`COS PR Approved`）：`allow_edit` 为 **All**；Desk **提交** 由 Client Script 显式挂载（Frappe 工具栏在有 Workflow 时 `can_submit` 恒假，见 `frappe/form/toolbar.js`）。须具备 DocPerm **submit**（如 `All`/`Logto User` 的 `if_owner`）。

驳回：见 ``COS PR Applicant Reject`` / ``COS PR Finance Reject`` / ``COS PR Director Reject``，
回落节点时由 ``payment_request_before_save`` 清理下游审批留痕字段。

**与工作流引擎的先后次序（Frappe ``frappe/model/document.py`` ``insert``）**：
``run_before_save_methods``（含 ``before_validate`` → DocType ``validate`` → ``before_save``）
先于 ``_validate()`` → ``validate_workflow()``（``frappe/model/workflow.py``）执行。
修订单若仍带父单的 ``COS PR Approved``，会在 ``validate_workflow`` 中与默认「草稿」逻辑冲突；
因此在 ``before_validate`` / DocType ``validate`` 钩子 / ``before_save`` 初段统一拉回 ``COS PR Draft``。

上线验证（dev→prod 按 migration 规范）：

1. migrate 后抽样新建 PR：Draft → 工作流至 COS PR Approved。
2. 终态中文标签为 **已批准**；打印「收付款申请 - 标准」签字区显示确认人/时间。
3. 存量未提交单：可 bench execute
   ``cos.cos_accounts.utils.payment_request_workflow_sync.sync_draft_payment_requests_to_initial_state``。
4. 取消后 ``workflow_state`` 写入 ``COS PR Cancelled``（界面「已取消」）；存量已取消单可 bench execute
   ``cos.cos_accounts.utils.payment_request_workflow_sync.sync_cancelled_payment_requests_workflow_state``。
5. **修订（Amend）** 产生的新草稿会复制父单 ``workflow_state``；在 ``before_validate`` / ``validate`` / ``before_save`` 拉回 ``COS PR Draft``。存量修订草稿可 bench execute
   ``cos.cos_accounts.utils.payment_request_workflow_sync.repair_amended_draft_payment_request_workflow_state``。

``before_submit`` 仍要求 ``workflow_state == COS PR Approved``（与界面是否展示「提交」无关）。
"""

from __future__ import annotations

import frappe
from frappe import _

WORKFLOW_DOC_NAME = "COS Payment Request Approval"
FINAL_STATE = "COS PR Approved"
STATE_PENDING_FINANCE = "COS PR Pending Finance"
STATE_PENDING_DIRECTOR = "COS PR Pending Director"
STATE_APPROVED = "COS PR Approved"
STATE_CANCELLED = "COS PR Cancelled"
INITIAL_STATE = "COS PR Draft"

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


def _clear_all_pr_approval_trail(doc) -> None:
	"""清空三级审批留痕（修订新草稿或回落草稿时使用）。"""
	for f in (
		"custom_pr_applicant_confirmed_by",
		"custom_pr_applicant_confirmed_on",
		"custom_pr_finance_approved_by",
		"custom_pr_finance_approved_on",
		"custom_pr_boss_approved_by",
		"custom_pr_boss_approved_on",
	):
		doc.set(f, None)


def _reset_amended_payment_request_to_draft(doc) -> bool:
	"""修订产生的新单（``amended_from``）入库前强制拉回 ``COS PR Draft``，避免 ``validate_workflow`` 带着复制来的终态与引擎打架。"""
	if not doc.is_new() or not doc.get("amended_from"):
		return False
	doc.set("workflow_state", INITIAL_STATE)
	_clear_all_pr_approval_trail(doc)
	return True


def payment_request_before_validate(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_payment_request_to_draft(doc)


def payment_request_validate(doc, method=None):
	"""紧接 ERPNext ``Payment Request.validate`` 之后再防守一次（避免控制器或其它扩展写回 workflow_state）。"""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	_reset_amended_payment_request_to_draft(doc)


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
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if _reset_amended_payment_request_to_draft(doc):
		return
	if doc.is_new():
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


def payment_request_on_cancel(doc, method=None):
	"""取消后把工作流状态写入「已取消」，避免界面仍显示终审「已批准」与修订按钮语义冲突。

	需在 Workflow 中存在 doc_status=2 的状态 ``COS PR Cancelled``（见 fixtures/workflow.json）。
	"""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	wname = frappe.db.get_value(
		"Workflow",
		{"document_type": "Payment Request", "is_active": 1},
		"name",
	)
	if wname != WORKFLOW_DOC_NAME:
		return
	frappe.db.set_value(
		"Payment Request",
		doc.name,
		"workflow_state",
		STATE_CANCELLED,
		update_modified=False,
	)
	doc.set("workflow_state", STATE_CANCELLED)

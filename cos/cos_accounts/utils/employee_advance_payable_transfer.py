# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""员工垫付采购：PI 提交后手动创建 JE（应付转员工），取消时自动取消已关联 JE。"""

from __future__ import annotations

import frappe
from frappe import _


def _get_pi_purchase_order(doc) -> str | None:
	"""获取 PI 关联的 PO。PI 表头无 purchase_order，需从子表 item 取。"""
	if doc.get("purchase_order"):
		return doc.purchase_order
	for item in doc.get("items") or []:
		if item.get("purchase_order"):
			return item.purchase_order
	return None


def _fetch_employee_advance_from_po(doc):
	"""从 PO 带出垫付标记与垫付员工。当 PI 有 purchase_order 且垫付信息未填时执行。"""
	po_name = _get_pi_purchase_order(doc)
	if not po_name:
		return
	# 任一垫付字段为空时从 PO 带出（覆盖 no_copy 导致的 mapper 不复制问题）
	if doc.get("custom_is_employee_advance") and doc.get("custom_advance_employee"):
		return
	po_advance = frappe.db.get_value(
		"Purchase Order",
		po_name,
		["custom_is_employee_advance", "custom_advance_employee"],
		as_dict=True,
	)
	if po_advance and po_advance.get("custom_is_employee_advance"):
		doc.custom_is_employee_advance = 1
		doc.custom_advance_employee = po_advance.get("custom_advance_employee")


def _get_advance_employee_editable_role() -> str | None:
	"""从采购设置获取可提交后修改垫付员工字段的角色。"""
	return frappe.db.get_single_value("Buying Settings", "custom_advance_employee_editable_role")


def _validate_advance_employee_edit_permission(doc):
	"""提交后修改垫付员工字段时，校验当前用户是否拥有采购设置中配置的角色。"""
	if doc.docstatus != 1:
		return
	role = _get_advance_employee_editable_role()
	if role:
		user_roles = {r.lower() for r in frappe.get_roles(frappe.session.user, include_default=True)}
		if role.lower() in user_roles:
			return
	# 检查是否修改了垫付相关字段
	old = frappe.db.get_value(
		doc.doctype,
		doc.name,
		["custom_is_employee_advance", "custom_advance_employee"],
		as_dict=True,
	)
	if not old:
		return
	if (
		doc.get("custom_is_employee_advance") != old.get("custom_is_employee_advance")
		or doc.get("custom_advance_employee") != old.get("custom_advance_employee")
	):
		frappe.throw(
			_("您无权限在提交后修改垫付员工相关字段。请在采购设置中配置「可修改垫付员工的角色」。"),
			title=_("无权限"),
		)


def on_purchase_invoice_validate(doc, method=None):
	"""PI 校验：员工垫付时必填垫付员工；从 PO 创建时带出垫付信息；提交后修改权限校验。"""
	_fetch_employee_advance_from_po(doc)

	if _should_create_payable_transfer_je(doc) and not doc.get("custom_advance_employee"):
		frappe.throw(
			_("已勾选「员工垫付」，请指定垫付员工"),
			title=_("员工垫付配置不完整"),
		)

	_validate_advance_employee_edit_permission(doc)


def validate_purchase_order_advance_employee(doc, method=None):
	"""PO 校验：提交后修改垫付员工字段时，校验当前用户是否在采购设置允许列表中。"""
	_validate_advance_employee_edit_permission(doc)


@frappe.whitelist()
def set_po_employee_advance(docname: str, is_advance: int = 1, employee: str = ""):
	"""直接更新 PO 员工垫付信息（绕过提交后修改校验，用于数据修复）。需 System Manager。"""
	frappe.only_for("System Manager")
	if not frappe.db.exists("Purchase Order", docname):
		frappe.throw(_("采购订单 {0} 不存在").format(docname))
	frappe.db.set_value(
		"Purchase Order",
		docname,
		{
			"custom_is_employee_advance": 1 if is_advance else 0,
			"custom_advance_employee": employee or None,
		},
		update_modified=True,
	)
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist()
def create_payable_transfer_je(docname: str):
	"""手动创建应付转员工 JE。PI 需已提交、勾选员工垫付且指定垫付员工。"""
	pi = frappe.get_doc("Purchase Invoice", docname)
	if pi.docstatus != 1:
		frappe.throw(_("采购发票需已提交"), title=_("无法创建"))
	if not _should_create_payable_transfer_je(pi):
		frappe.throw(_("请勾选「员工垫付」"), title=_("无法创建"))
	employee = pi.get("custom_advance_employee")
	if not employee:
		frappe.throw(_("请指定垫付员工"), title=_("无法创建"))
	if pi.get("custom_payable_transfer_je"):
		frappe.throw(
			_("已存在应付转员工日记账 {0}").format(
				frappe.utils.get_link_to_form("Journal Entry", pi.custom_payable_transfer_je)
			),
			title=_("已创建"),
		)

	je = _create_payable_transfer_journal_entry(pi, employee)
	if je:
		frappe.db.set_value(
			"Purchase Invoice",
			pi.name,
			{"custom_payable_transfer_je": je.name, "custom_employee_reimbursed": "未报销"},
			update_modified=False,
		)
		return {"journal_entry": je.name}
	return None


def purchase_invoice_before_cancel(doc, method=None):
	"""PI 取消前：先取消应付转员工 JE（若有），再执行税务登记等联动。"""
	_on_purchase_invoice_cancel(doc, method)
	# 链式调用税务登记联动（避免链接校验拦截）
	from cos.cos_accounts.utils.tax_registry_reference import invoice_before_cancel as _tax_cancel

	_tax_cancel(doc, method)


def _on_purchase_invoice_cancel(doc, method=None):
	"""PI 取消前：若存在已关联的应付转员工 JE，先取消该 JE。"""
	je_name = doc.get("custom_payable_transfer_je")
	if not je_name:
		return

	je = frappe.get_doc("Journal Entry", je_name)
	if je.docstatus != 1:
		return

	je.flags.ignore_permissions = True
	je.cancel()
	frappe.db.set_value(
		"Purchase Invoice",
		doc.name,
		"custom_payable_transfer_je",
		"",
		update_modified=False,
	)
	frappe.msgprint(
		_("已取消应付转员工日记账：{0}").format(je_name),
		indicator="orange",
	)


def payment_entry_on_submit(doc, method=None):
	"""PE 提交后：若 references 引用应付转员工 JE，将对应 PI 的 custom_employee_reimbursed 置「已报销」。"""
	for ref in doc.get("references") or []:
		if ref.get("reference_doctype") == "Journal Entry" and ref.get("reference_name"):
			_update_pi_employee_reimbursed(ref.reference_name, status="已报销")


def payment_entry_on_cancel(doc, method=None):
	"""PE 取消后：若 references 引用应付转员工 JE，且无其他已提交 PE 引用该 JE，将对应 PI 置「未报销」。"""
	for ref in doc.get("references") or []:
		if ref.get("reference_doctype") == "Journal Entry" and ref.get("reference_name"):
			je_name = ref.reference_name
			if _has_other_submitted_pe_for_je(je_name, exclude_pe=doc.name):
				continue
			_update_pi_employee_reimbursed(je_name, status="未报销")


def _update_pi_employee_reimbursed(je_name: str, status: str):
	"""将 custom_payable_transfer_je=je_name 的 PI 的 custom_employee_reimbursed 更新（未报销/已报销）。"""
	pi_names = frappe.get_all(
		"Purchase Invoice",
		filters={"custom_payable_transfer_je": je_name, "docstatus": 1},
		pluck="name",
	)
	for name in pi_names:
		frappe.db.set_value(
			"Purchase Invoice",
			name,
			"custom_employee_reimbursed",
			status,
			update_modified=False,
		)


def _has_other_submitted_pe_for_je(je_name: str, exclude_pe: str) -> bool:
	"""是否存在其他已提交的 PE 引用该 JE。"""
	refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"reference_doctype": "Journal Entry",
			"reference_name": je_name,
			"parent": ["!=", exclude_pe],
		},
		fields=["parent"],
		pluck="parent",
	)
	for pe_name in set(refs):
		if frappe.db.get_value("Payment Entry", pe_name, "docstatus") == 1:
			return True
	return False


def _should_create_payable_transfer_je(doc) -> bool:
	"""判断是否需创建应付转员工 JE。"""
	return bool(doc.get("custom_is_employee_advance"))


def _create_payable_transfer_journal_entry(pi_doc, employee: str):
	"""创建 JE：借应付供应商 贷应付员工（party=员工）。"""
	from frappe.utils import flt

	# 金额与 PI 的 supplier GL 一致
	base_amount = (
		flt(pi_doc.base_rounded_total)
		if (pi_doc.rounding_adjustment and pi_doc.base_rounded_total)
		else flt(pi_doc.base_grand_total)
	)
	if base_amount <= 0:
		return None

	# 科目：借方=PI 的 credit_to（应付供应商），贷方=公司默认员工报销应付
	supplier_payable = pi_doc.credit_to
	employee_payable = frappe.get_cached_value(
		"Company",
		pi_doc.company,
		"default_expense_claim_payable_account",
	)
	if not employee_payable:
		frappe.throw(
			_("公司 {0} 未配置「员工报销应付」科目，无法创建应付转员工 JE").format(
				pi_doc.company
			),
			title=_("科目配置缺失"),
		)

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = pi_doc.company
	je.posting_date = pi_doc.posting_date
	je.user_remark = _("应付转员工：PI {0}，PO {1}").format(
		pi_doc.name,
		pi_doc.get("purchase_order") or "-",
	)
	je.is_system_generated = 1

	# 借方：应付供应商
	je.append(
		"accounts",
		{
			"account": supplier_payable,
			"party_type": "Supplier",
			"party": pi_doc.supplier,
			"debit_in_account_currency": base_amount,
			"debit": base_amount,
			"cost_center": pi_doc.cost_center,
			"project": pi_doc.project,
			"against": employee_payable,
			"reference_type": "Purchase Invoice",
			"reference_name": pi_doc.name,
		},
	)

	# 贷方：应付员工（不设 reference_type/reference_name，避免 validate_reference_doc 校验失败：
	# 该行 party=员工、account=应付员工，与 PI 的 Supplier/Credit To 不匹配）
	je.append(
		"accounts",
		{
			"account": employee_payable,
			"party_type": "Employee",
			"party": employee,
			"credit_in_account_currency": base_amount,
			"credit": base_amount,
			"cost_center": pi_doc.cost_center,
			"project": pi_doc.project,
			"against": supplier_payable,
		},
	)

	je.flags.ignore_permissions = True
	je.submit()
	return je


def _build_employee_advance_payment_doc(pi, paid_from: str):
	"""构建付给员工 PE 文档（不 insert）。"""
	from frappe.utils import flt

	from erpnext.accounts.party import get_party_account

	employee = pi.custom_advance_employee
	company = pi.company
	base_amount = (
		flt(pi.base_rounded_total)
		if (pi.rounding_adjustment and pi.base_rounded_total)
		else flt(pi.base_grand_total)
	)
	je_name = pi.get("custom_payable_transfer_je")
	paid_to = get_party_account("Employee", employee, company)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.party_type = "Employee"
	pe.party = employee
	pe.party_name = frappe.db.get_value("Employee", employee, "employee_name") or employee
	pe.company = company
	pe.posting_date = pi.posting_date
	pe.paid_from = paid_from
	pe.paid_to = paid_to
	# 源科目货币、目标科目货币、科目类型（必填，从科目带出）
	paid_from_acc = frappe.db.get_value(
		"Account", paid_from, ["account_currency", "account_type"], as_dict=True
	)
	paid_to_acc = frappe.db.get_value(
		"Account", paid_to, ["account_currency", "account_type"], as_dict=True
	)
	default_currency = frappe.get_cached_value("Company", company, "default_currency")
	pe.paid_from_account_currency = (paid_from_acc and paid_from_acc.account_currency) or default_currency
	pe.paid_to_account_currency = (paid_to_acc and paid_to_acc.account_currency) or pe.paid_from_account_currency
	pe.paid_from_account_type = paid_from_acc and paid_from_acc.account_type
	pe.paid_to_account_type = paid_to_acc and paid_to_acc.account_type
	pe.paid_amount = base_amount
	pe.received_amount = base_amount
	# 业务单号留空；默认现金科目时不必填，用户可切换银行后填写
	pe.reference_date = pi.posting_date
	pe.remarks = _("应付转员工后付给员工：PI {0}，JE {1}").format(pi.name, je_name)

	pe.append(
		"references",
		{
			"reference_doctype": "Journal Entry",
			"reference_name": je_name,
			"allocated_amount": base_amount,
			"total_amount": base_amount,
			"outstanding_amount": base_amount,
			"exchange_rate": 1,
		},
	)
	return pe


@frappe.whitelist()
def get_employee_advance_payment_draft_data(docname: str):
	"""返回付给员工 PE 的草稿数据（不 insert），供客户端用 frappe.new_doc 打开。
	默认使用现金科目，业务单号可留空，用户保存草稿后按需填写。
	"""
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

	pi = frappe.get_doc("Purchase Invoice", docname)
	if pi.docstatus != 1:
		frappe.throw(_("采购发票需已提交"), title=_("无法创建"))
	if not pi.get("custom_is_employee_advance") or not pi.get("custom_advance_employee"):
		frappe.throw(_("仅支持员工垫付发票"), title=_("无法创建"))
	if not pi.get("custom_payable_transfer_je"):
		frappe.throw(_("请先创建应付转员工日记账"), title=_("无法创建"))
	from frappe.utils import flt
	base_amount = (
		flt(pi.base_rounded_total)
		if (pi.rounding_adjustment and pi.base_rounded_total)
		else flt(pi.base_grand_total)
	)
	if base_amount <= 0:
		frappe.throw(_("发票金额无效"), title=_("无法创建"))

	# 优先现金科目，避免银行科目必填业务单号导致无法保存草稿
	cash_info = get_default_bank_cash_account(pi.company, "Cash", fetch_balance=False)
	if not cash_info or not cash_info.get("account"):
		bank_info = get_default_bank_cash_account(pi.company, "Bank", fetch_balance=False)
		if not bank_info or not bank_info.get("account"):
			frappe.throw(
				_("公司 {0} 未配置默认现金/银行账户").format(pi.company),
				title=_("无法创建"),
			)
		paid_from = bank_info.account
	else:
		paid_from = cash_info.account

	pe = _build_employee_advance_payment_doc(pi, paid_from)
	d = pe.as_dict()
	d.pop("name", None)  # 由客户端生成新 doc 名称
	return d


@frappe.whitelist()
def create_employee_advance_payment(docname: str):
	"""从 PI 创建「付给员工」Payment Entry（服务端 insert，保留兼容）。"""
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

	pi = frappe.get_doc("Purchase Invoice", docname)
	if pi.docstatus != 1:
		frappe.throw(_("采购发票需已提交"), title=_("无法创建"))
	if not pi.get("custom_is_employee_advance") or not pi.get("custom_advance_employee"):
		frappe.throw(_("仅支持员工垫付发票"), title=_("无法创建"))
	je_name = pi.get("custom_payable_transfer_je")
	if not je_name:
		frappe.throw(_("请先创建应付转员工日记账"), title=_("无法创建"))
	from frappe.utils import flt
	base_amount = (
		flt(pi.base_rounded_total)
		if (pi.rounding_adjustment and pi.base_rounded_total)
		else flt(pi.base_grand_total)
	)
	if base_amount <= 0:
		frappe.throw(_("发票金额无效"), title=_("无法创建"))

	bank_info = get_default_bank_cash_account(pi.company, "Bank", fetch_balance=False)
	if not bank_info or not bank_info.get("account"):
		bank_info = get_default_bank_cash_account(pi.company, "Cash", fetch_balance=False)
	if not bank_info or not bank_info.get("account"):
		frappe.throw(
			_("公司 {0} 未配置默认银行/现金账户").format(pi.company),
			title=_("无法创建"),
		)
	paid_from = bank_info.account

	pe = _build_employee_advance_payment_doc(pi, paid_from)
	pe.reference_no = _("待填写")  # 银行科目必填，预填占位符
	pe.flags.ignore_permissions = True
	pe.insert()
	return {"payment_entry": pe.name}

# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""员工垫付采购：PI 提交时自动创建 JE（应付转员工），取消时自动取消 JE。"""

from __future__ import annotations

import frappe
from frappe import _


def _fetch_employee_advance_from_po(doc):
	"""从 PO 带出垫付标记与垫付员工。当 PI 有 purchase_order 且垫付信息未填时执行。"""
	if not doc.get("purchase_order"):
		return
	# 任一垫付字段为空时从 PO 带出（覆盖 no_copy 导致的 mapper 不复制问题）
	if doc.get("custom_is_employee_advance") and doc.get("custom_advance_employee"):
		return
	po_advance = frappe.db.get_value(
		"Purchase Order",
		doc.purchase_order,
		["custom_is_employee_advance", "custom_advance_employee"],
		as_dict=True,
	)
	if po_advance and po_advance.get("custom_is_employee_advance"):
		doc.custom_is_employee_advance = 1
		doc.custom_advance_employee = po_advance.get("custom_advance_employee")


def on_purchase_invoice_validate(doc, method=None):
	"""PI 校验：员工垫付时必填垫付员工；从 PO 创建时带出垫付信息。"""
	_fetch_employee_advance_from_po(doc)

	if _should_create_payable_transfer_je(doc) and not doc.get("custom_advance_employee"):
		frappe.throw(
			_("已勾选「员工垫付」，请指定垫付员工"),
			title=_("员工垫付配置不完整"),
		)


def on_purchase_invoice_submit(doc, method=None):
	"""PI 提交后：若勾选员工垫付且指定垫付员工，自动创建 JE 应付转员工。"""
	if not _should_create_payable_transfer_je(doc):
		return

	employee = doc.get("custom_advance_employee")
	if not employee:
		return  # validate 已校验，此处不应出现

	je = _create_payable_transfer_journal_entry(doc, employee)
	if je:
		frappe.db.set_value(
			"Purchase Invoice",
			doc.name,
			"custom_payable_transfer_je",
			je.name,
			update_modified=False,
		)
		frappe.msgprint(
			_("已自动创建应付转员工日记账：{0}").format(
				frappe.utils.get_link_to_form("Journal Entry", je.name)
			),
			indicator="blue",
		)


def purchase_invoice_before_cancel(doc, method=None):
	"""PI 取消前：先取消应付转员工 JE（若有），再执行税务登记等联动。"""
	_on_purchase_invoice_cancel(doc, method)
	# 链式调用税务登记联动（避免链接校验拦截）
	from cos.cos_accounts.utils.tax_registry_reference import invoice_before_cancel as _tax_cancel

	_tax_cancel(doc, method)


def _on_purchase_invoice_cancel(doc, method=None):
	"""PI 取消前：若存在自动创建的 JE，先取消该 JE。"""
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
		_("已自动取消应付转员工日记账：{0}").format(je_name),
		indicator="orange",
	)


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

	# 贷方：应付员工
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
			"reference_type": "Purchase Invoice",
			"reference_name": pi_doc.name,
		},
	)

	je.flags.ignore_permissions = True
	je.submit()
	return je

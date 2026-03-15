# Copyright (c) 2026, COS and contributors
# License: MIT. See license.txt

"""采购订单、供应商报价、采购入库提交后税费变更。"""

import frappe
from frappe import _
from frappe.utils import flt

# 支持的 DocType 与对应税费模板
_PURCHASE_DOCTYPES = {
	"Purchase Order": "Purchase Taxes and Charges Template",
	"Supplier Quotation": "Purchase Taxes and Charges Template",
	"Purchase Receipt": "Purchase Taxes and Charges Template",
}


def _can_update(doctype: str, docname: str) -> bool:
	if not doctype or not docname:
		return False
	if doctype not in _PURCHASE_DOCTYPES:
		return False
	doc = frappe.get_cached_doc(doctype, docname)
	if doc.docstatus != 1:
		return False
	if not frappe.has_permission(doctype, "write", doc):
		return False
	if doctype == "Purchase Order":
		if getattr(doc, "status", None) == "Closed":
			return False
		if flt(getattr(doc, "per_received", 0)) >= 100:
			return False
	if doctype == "Purchase Receipt":
		if flt(getattr(doc, "per_billed", 0)) > 0:
			return False
	return True


@frappe.whitelist()
def can_update_purchase_taxes(doctype: str, docname: str) -> bool:
	"""是否允许变更采购类单据税费。供前端使用。"""
	return _can_update(doctype, docname)


@frappe.whitelist()
def update_purchase_taxes(
	doctype: str,
	docname: str,
	taxes_and_charges: str | None = None,
	tax_category: str | None = None,
) -> None:
	"""更新采购类单据税费（提交后）。支持切换税费模板与税种。"""
	if not doctype or not docname:
		frappe.throw(_("单据类型与名称不能为空"))
	if doctype not in _PURCHASE_DOCTYPES:
		frappe.throw(_("不支持的单据类型：{0}").format(doctype))

	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")

	if not _can_update(doctype, docname):
		frappe.throw(_("当前状态不允许变更税费。"))

	if doctype == "Purchase Receipt" and flt(doc.per_billed) > 0:
		frappe.throw(_("采购入库已部分或全部开票，不可修改税费。"))

	changed = False
	template_doctype = _PURCHASE_DOCTYPES[doctype]

	if taxes_and_charges is not None:
		taxes_and_charges = (taxes_and_charges or "").strip()
		if doc.taxes_and_charges != taxes_and_charges:
			doc.taxes_and_charges = taxes_and_charges or None
			doc.set("taxes", [])
			if doc.taxes_and_charges:
				from erpnext.controllers.accounts_controller import get_taxes_and_charges

				taxes = get_taxes_and_charges(template_doctype, doc.taxes_and_charges)
				doc.extend("taxes", taxes)
			changed = True

	if tax_category is not None and doc.meta.has_field("tax_category"):
		tax_category = (tax_category or "").strip()
		if doc.tax_category != tax_category:
			doc.tax_category = tax_category or None
			changed = True

	if not changed:
		return

	doc.flags.ignore_validate_update_after_submit = True
	doc.calculate_taxes_and_totals()
	doc.set_total_in_words()
	if doctype == "Purchase Order":
		doc.set_payment_schedule()
	doc.save()

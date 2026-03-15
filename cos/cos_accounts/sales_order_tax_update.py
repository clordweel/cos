# Copyright (c) 2026, COS and contributors
# License: MIT. See license.txt

"""销售订单提交后税费变更。"""

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def can_update_sales_order_taxes(so_name: str) -> bool:
	"""是否允许变更销售订单税费。供前端使用。"""
	if not so_name:
		return False
	so = frappe.get_cached_doc("Sales Order", so_name)
	if so.docstatus != 1:
		return False
	if so.status == "Closed":
		return False
	if flt(so.per_delivered) >= 100 or flt(so.per_billed) >= 100:
		return False
	return frappe.has_permission("Sales Order", "write", so)


@frappe.whitelist()
def update_sales_order_taxes(
	so_name: str,
	taxes_and_charges: str | None = None,
	tax_category: str | None = None,
) -> None:
	"""更新销售订单税费（提交后）。支持切换税费模板与税种。"""
	if not so_name:
		frappe.throw(_("销售订单名称不能为空"))

	so = frappe.get_doc("Sales Order", so_name)
	so.check_permission("write")

	if not can_update_sales_order_taxes(so_name):
		frappe.throw(
			_("当前状态不允许变更税费：订单已关闭、已全部交货或已全部开票时不可修改。")
		)

	# per_billed > 0 时禁止，避免与已开票金额不一致
	if flt(so.per_billed) > 0:
		frappe.throw(
			_("订单已部分或全部开票，不可修改税费。已开票金额与订单税额可能不一致。")
		)

	changed = False

	if taxes_and_charges is not None:
		taxes_and_charges = (taxes_and_charges or "").strip()
		if so.taxes_and_charges != taxes_and_charges:
			so.taxes_and_charges = taxes_and_charges or None
			# 从模板重新拉取税费行
			so.set("taxes", [])
			if so.taxes_and_charges:
				from erpnext.controllers.accounts_controller import get_taxes_and_charges

				taxes = get_taxes_and_charges("Sales Taxes and Charges Template", so.taxes_and_charges)
				so.extend("taxes", taxes)
			changed = True

	if tax_category is not None:
		tax_category = (tax_category or "").strip()
		if so.tax_category != tax_category:
			so.tax_category = tax_category or None
			changed = True

	if not changed:
		return

	so.flags.ignore_validate_update_after_submit = True
	so.calculate_taxes_and_totals()
	so.set_total_in_words()
	so.set_payment_schedule()
	so.save()

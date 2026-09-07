# Copyright (c) 2026, COS and contributors
# License: MIT. See license.txt

"""采购订单提交后、付全款前允许改物料单价。"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt
from erpnext.controllers.accounts_controller import (
	update_child_qty_rate as erpnext_update_child_qty_rate,
)


def payable_total(doc) -> float:
	if not cint(getattr(doc, "disable_rounded_total", 0)):
		rounded = flt(getattr(doc, "rounded_total", 0))
		if rounded:
			return rounded
	return flt(getattr(doc, "grand_total", 0))


def is_purchase_order_fully_paid(doc) -> bool:
	total = payable_total(doc)
	if total <= 0:
		return False
	return flt(getattr(doc, "advance_paid", 0)) >= total


def assert_po_item_rates_editable(doc) -> None:
	if doc.doctype != "Purchase Order":
		return
	if doc.docstatus != 1:
		frappe.throw(_("仅已提交的采购订单可以修改单价"))
	if getattr(doc, "status", None) == "Closed":
		frappe.throw(_("已关闭的采购订单不能修改单价"))
	if is_purchase_order_fully_paid(doc):
		frappe.throw(_("已付全款，不能再修改采购订单物料单价"))


@frappe.whitelist()
def update_child_qty_rate(parent_doctype, trans_items, parent_doctype_name, child_docname="items"):
	"""拦截 ERPNext 更新明细：采购订单付全款后禁止改价。"""
	if parent_doctype == "Purchase Order" and parent_doctype_name:
		doc = frappe.get_doc(parent_doctype, parent_doctype_name)
		doc.check_permission("write")
		assert_po_item_rates_editable(doc)
	return erpnext_update_child_qty_rate(
		parent_doctype, trans_items, parent_doctype_name, child_docname=child_docname
	)

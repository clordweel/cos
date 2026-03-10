# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""从 PO 创建 PI 时带出员工垫付信息。"""

from __future__ import annotations

import frappe

from cos.cos_accounts.utils.employee_advance_payable_transfer import _fetch_employee_advance_from_po


def make_purchase_invoice(source_name, target_doc=None, args=None):
	"""包装 ERPNext 的 make_purchase_invoice，在返回前从 PO 带出垫付信息。"""
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice as _original

	doc = _original(source_name, target_doc, args)
	_fetch_employee_advance_from_po(doc)
	return doc

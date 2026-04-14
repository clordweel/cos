# Copyright (c) 2026, COS and contributors
"""将打印格式「采购订单 - 代发货单」重命名为「采购订单 - 直发单」（与 fixtures 一致）。"""

from __future__ import annotations

import frappe


def execute():
	old = "采购订单 - 代发货单"
	new = "采购订单 - 直发单"
	if frappe.db.exists("Print Format", new):
		return
	if not frappe.db.exists("Print Format", old):
		return
	frappe.rename_doc("Print Format", old, new, merge=False, force=True)
	frappe.db.commit()
	from cos.scripts.sync_purchase_order_proxy_delivery_print_format import sync as sync_po

	try:
		sync_po()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped after rename to 采购订单 - 直发单",
			message=str(e),
		)
	frappe.db.commit()

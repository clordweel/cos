# Copyright (c) 2026, COS and contributors
"""同步「采购订单 - 直发单」模板：收货信息区图2布局（地址标签独行、联系人/电话）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_purchase_order_proxy_delivery_print_format import sync as sync_po

	try:
		sync_po()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: purchase order direct ship v5",
			message=str(e),
		)
	frappe.db.commit()

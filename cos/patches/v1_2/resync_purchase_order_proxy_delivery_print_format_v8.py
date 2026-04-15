# Copyright (c) 2026, COS and contributors
"""同步「采购订单 - 直发单」模板：收货地址并入基本信息表，标签/值排版与各行一致。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_purchase_order_proxy_delivery_print_format import sync as sync_po

	try:
		sync_po()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: purchase order direct ship v8",
			message=str(e),
		)
	frappe.db.commit()

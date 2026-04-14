# Copyright (c) 2026, COS and contributors
"""再次从仓库同步「采购订单 - 直发单」模板（收货信息、项目客户、页脚声明等）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_purchase_order_proxy_delivery_print_format import sync as sync_po_proxy

	try:
		sync_po_proxy()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: purchase order proxy delivery v2",
			message=str(e),
		)
	frappe.db.commit()

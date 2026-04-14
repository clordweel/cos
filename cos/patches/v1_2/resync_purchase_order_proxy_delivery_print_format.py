# Copyright (c) 2026, COS and contributors
"""将「采购订单 - 代发货单」打印模板从仓库文件同步到数据库。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_purchase_order_proxy_delivery_print_format import sync as sync_po_proxy

	try:
		sync_po_proxy()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: purchase order proxy delivery",
			message=str(e),
		)
	frappe.db.commit()

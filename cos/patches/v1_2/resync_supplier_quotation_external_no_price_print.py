# Copyright (c) 2026, COS and contributors
"""创建/更新「供应商报价单 - 外部（无价格）」打印格式（无单价、金额与汇总区）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_supplier_quotation_external_no_price import sync as sync_sq_external_no_price

	try:
		sync_sq_external_no_price()
	except FileNotFoundError:
		frappe.log_error(
			title="Print Format sync skipped: supplier quotation external no price",
			message="template or styles.css missing",
		)
	frappe.db.commit()

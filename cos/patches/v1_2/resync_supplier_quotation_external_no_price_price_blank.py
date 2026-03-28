# Copyright (c) 2026, COS and contributors
"""重新同步「供应商报价单 - 外部（无价格）」：保留价税列与汇总区，格内始终留空供供应商填写。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_supplier_quotation_external_no_price import sync as sync_sq_external_no_price

	try:
		sync_sq_external_no_price()
	except FileNotFoundError:
		frappe.log_error(
			title="Print Format sync skipped: supplier quotation external price blank",
			message="template or styles.css missing",
		)
	frappe.db.commit()

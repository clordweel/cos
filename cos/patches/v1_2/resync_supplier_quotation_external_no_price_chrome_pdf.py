# Copyright (c) 2026, COS and contributors
"""将「供应商报价单 - 外部（无价格）」PDF 引擎改为 Chrome 并同步模板（修复与「外部」版渲染不一致问题）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_supplier_quotation_external_no_price import sync as sync_sq_external_no_price

	try:
		sync_sq_external_no_price()
	except FileNotFoundError:
		frappe.log_error(
			title="Print Format sync skipped: supplier quotation external no price (chrome pdf)",
			message="template or styles.css missing",
		)
	frappe.db.commit()

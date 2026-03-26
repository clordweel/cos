# Copyright (c) 2026, COS and contributors
"""同步「供应商报价单 - 外部」打印模板：已填单价/合计时在打印中带出，未填时仍留空。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_supplier_quotation_external import sync as sync_sq_external

	try:
		sync_sq_external()
	except FileNotFoundError:
		frappe.log_error(
			title="Print Format sync skipped: supplier quotation external",
			message="template or styles.css missing",
		)
	frappe.db.commit()

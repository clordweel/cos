# Copyright (c) 2026, COS and contributors
"""再次同步购销合同打印模板（公章改为 data URI，修复 PDF 不显示）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_contract_po_so_print_formats import sync as sync_contract

	try:
		sync_contract()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: contract PO/SO (data uri)",
			message=str(e),
		)
	frappe.db.commit()

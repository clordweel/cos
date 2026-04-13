# Copyright (c) 2026, COS and contributors
"""同步购销合同打印模板（公章尺寸与叠放位置调整）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_contract_po_so_print_formats import sync as sync_contract

	try:
		sync_contract()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: contract PO/SO (seal layout)",
			message=str(e),
		)
	frappe.db.commit()

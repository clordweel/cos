# Copyright (c) 2026, COS and contributors
"""将采购/销售合同「通用」打印模板从仓库文件同步到数据库（含公章叠放等模板更新）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_contract_po_so_print_formats import sync as sync_contract

	try:
		sync_contract()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: contract PO/SO",
			message=str(e),
		)
	frappe.db.commit()

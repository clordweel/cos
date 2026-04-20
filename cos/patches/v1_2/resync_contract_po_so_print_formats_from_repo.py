# Copyright (c) 2026, COS and contributors
"""从仓库 print_format 目录将采购/销售合同类及工业 A4 模板写回数据库 Print Format。

在「fixture 已更新但站点仍显示旧版」或拉代码后未手动 execute sync 时，由 migrate 再执行一次确保生效。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_contract_po_so_print_formats import sync as sync_contract

	try:
		sync_contract()
	except FileNotFoundError as e:
		frappe.log_error(
			title="Print Format sync skipped: contract PO/SO/industrial A4",
			message=str(e),
		)
	frappe.db.commit()

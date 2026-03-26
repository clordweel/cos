# Copyright (c) 2026, COS and contributors
"""将「供应商报价单 - 标准」打印模板从仓库文件同步到数据库（未填单价时行与汇总金额显示为空）。"""

from __future__ import annotations

import frappe


def execute():
	from cos.scripts.sync_supplier_quotation_print_format import sync as sync_sq_standard

	try:
		sync_sq_standard()
	except FileNotFoundError:
		frappe.log_error(
			title="Print Format sync skipped: supplier quotation standard",
			message="template or styles.css missing",
		)
	frappe.db.commit()

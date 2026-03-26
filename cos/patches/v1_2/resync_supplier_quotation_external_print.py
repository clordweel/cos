# Copyright (c) 2026, COS and contributors
"""将「供应商报价单 - 外部」打印模板从仓库文件重新同步到数据库（修正物料信息与备注列重复）。"""

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

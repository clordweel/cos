# Copyright (c) 2026, COS and contributors
"""为 Item Purchase Source 子表添加 is_primary 字段，用于标识主采购链接。"""

import frappe
from frappe.database.schema import add_column


def execute():
	if not frappe.db.exists("DocType", "Item Purchase Source"):
		return
	# 检查列是否已存在（DocType 同步可能已添加）
	if frappe.db.has_column("Item Purchase Source", "is_primary"):
		return
	add_column("Item Purchase Source", "is_primary", "Check", default="0")
	frappe.db.commit()

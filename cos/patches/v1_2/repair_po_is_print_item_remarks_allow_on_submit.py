# Copyright (c) 2026, COS and contributors
"""确保 Purchase Order「是否打印物料备注」字段允许提交后修改（补丁 ensure 已执行过的站点不会重跑）。"""

from __future__ import annotations

import frappe


def execute():
	name = "Purchase Order-custom_is_print_item_remarks"
	if not frappe.db.exists("Custom Field", name):
		return
	cf = frappe.get_doc("Custom Field", name)
	if int(cf.allow_on_submit or 0) == 1:
		return
	cf.allow_on_submit = 1
	cf.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype="Purchase Order")

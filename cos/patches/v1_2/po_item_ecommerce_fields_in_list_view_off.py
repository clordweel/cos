# Copyright (c) 2026, COS and contributors
"""采购订单明细行：电商相关自定义字段（采购平台、平台 SKU、采购链接）不在子表列表默认列中显示。"""

from __future__ import annotations

import frappe


def execute():
	names = (
		"Purchase Order Item-custom_platform",
		"Purchase Order Item-custom_platform_sku",
		"Purchase Order Item-custom_purchase_url",
	)
	for name in names:
		if frappe.db.exists("Custom Field", name):
			frappe.db.set_value("Custom Field", name, "in_list_view", 0)

	frappe.clear_cache(doctype="Purchase Order")
	frappe.db.commit()

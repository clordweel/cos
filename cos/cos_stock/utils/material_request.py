# Copyright (c) 2025, COS and contributors
# License: MIT. See license.txt

"""物料需求单（Material Request）校验：禁止提交含虚拟占位物料的 MR。"""

import frappe
from frappe import _


def validate_no_virtual_items_in_material_request(doc, method=None):
	"""提交前校验：明细中不得包含标记为虚拟物料的 Item。

	虚拟物料（custom_is_virtual_item=1）仅用于草稿占位，需先转换为真实物料后再提交。
	"""
	if not doc.items:
		return
	item_codes = [row.item_code for row in doc.items if row.item_code]
	if not item_codes:
		return
	virtual_items = frappe.db.get_all(
		"Item",
		filters={"name": ["in", item_codes], "custom_is_virtual_item": 1},
		pluck="name",
	)
	if virtual_items:
		names = ", ".join(virtual_items)
		frappe.throw(
			_("物料需求单中不得包含虚拟占位物料，请先转换为真实物料后再提交。涉及：{0}").format(names),
			exc=frappe.ValidationError,
		)

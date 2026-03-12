# Copyright (c) 2025, COS and contributors
# License: MIT. See license.txt

"""物料需求单（Material Request）校验：禁止提交含虚拟占位物料的 MR。"""

import frappe
from frappe import _


def can_update_material_request_items(mr_name: str) -> bool:
	"""是否允许变更物料需求单明细（提交后）。供 onload 与前端使用。"""
	if not mr_name:
		return False
	mr = frappe.get_cached_doc("Material Request", mr_name)
	if mr.docstatus != 1:
		return False
	if mr.status in ("Stopped", "Cancelled"):
		return False
	return frappe.has_permission("Material Request", "write", mr)


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

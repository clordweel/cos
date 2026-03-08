# Copyright (c) 2025, BIoT and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class ItemBaseName(NestedSet):
	pass


@frappe.whitelist()
def fill_empty_abbreviations():
	"""为缩写为空的基础名按映射补填缩写（英文优先+唯一性）。返回更新条数。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import run_fill_abbreviations

	return run_fill_abbreviations()

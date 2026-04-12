# Copyright (c) 2026, COS and contributors
"""将历史「型号系列」单字段 custom_model_series 拆为「产品系列」「型号」；数据迁入产品系列后删除旧字段。"""

from __future__ import annotations

import json

import frappe


def execute():
	if not frappe.db.exists("DocType", "Item"):
		return

	legacy = "Item-custom_model_series"
	has_legacy_cf = frappe.db.exists("Custom Field", legacy)
	has_legacy_col = frappe.db.has_column("Item", "custom_model_series")

	# 先确保新字段存在（与 ensure_item 补丁一致）
	ps_name = "Item-custom_product_series"
	if not frappe.db.exists("Custom Field", ps_name):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"module": "COS Share",
				"fieldname": "custom_product_series",
				"fieldtype": "Data",
				"label": "产品系列",
				"description": "产品线或系列族标识（如系列代号、代际），与「型号」「规格参数」区分。",
				"insert_after": "custom_tech_standard_number",
				"allow_in_quick_entry": 1,
				"in_preview": 1,
			}
		).insert(ignore_permissions=True)

	mn_name = "Item-custom_model_number"
	if not frappe.db.exists("Custom Field", mn_name):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"module": "COS Share",
				"fieldname": "custom_model_number",
				"fieldtype": "Data",
				"label": "型号",
				"description": "制造商目录型号或订货型号（与「产品系列」区分）。",
				"insert_after": "custom_product_series",
				"allow_in_quick_entry": 1,
				"in_preview": 1,
			}
		).insert(ignore_permissions=True)

	# 旧列数据并入「产品系列」（合并字段无法可靠自动拆分）
	if has_legacy_col and frappe.db.has_column("Item", "custom_product_series"):
		frappe.db.sql(
			"""
			UPDATE `tabItem`
			SET `custom_product_series` = `custom_model_series`
			WHERE IFNULL(`custom_model_series`, '') != ''
			  AND IFNULL(`custom_product_series`, '') = ''
			"""
		)

	if has_legacy_cf:
		frappe.delete_doc("Custom Field", legacy, force=True, ignore_permissions=True)

	frappe.db.set_value("Custom Field", ps_name, "insert_after", "custom_tech_standard_number")
	frappe.db.set_value("Custom Field", mn_name, "insert_after", "custom_product_series")
	if frappe.db.exists("Custom Field", "Item-custom_specification"):
		frappe.db.set_value(
			"Custom Field",
			"Item-custom_specification",
			"insert_after",
			"custom_model_number",
		)

	if frappe.db.exists("Property Setter", "Item-main-search_fields"):
		cur = frappe.db.get_value("Property Setter", "Item-main-search_fields", "value") or ""
		parts = [p.strip() for p in cur.split(",") if p.strip()]
		parts = [p for p in parts if p != "custom_model_series"]
		for fname in ("custom_product_series", "custom_model_number"):
			if fname not in parts:
				try:
					idx = parts.index("custom_specification")
					parts.insert(idx, fname)
				except ValueError:
					parts.append(fname)
		frappe.db.set_value(
			"Property Setter",
			"Item-main-search_fields",
			"value",
			",".join(parts),
		)

	if frappe.db.exists("Property Setter", "Item-main-field_order"):
		raw = frappe.db.get_value("Property Setter", "Item-main-field_order", "value") or "[]"
		try:
			order = json.loads(raw)
		except json.JSONDecodeError:
			order = []
		if isinstance(order, list):
			order = [f for f in order if f != "custom_model_series"]
			if "custom_product_series" not in order:
				try:
					i = order.index("custom_tech_standard_number")
					order.insert(i + 1, "custom_product_series")
				except ValueError:
					pass
			if "custom_model_number" not in order:
				try:
					j = order.index("custom_product_series")
					order.insert(j + 1, "custom_model_number")
				except ValueError:
					pass
			frappe.db.set_value(
				"Property Setter",
				"Item-main-field_order",
				"value",
				json.dumps(order, ensure_ascii=False),
			)

	frappe.clear_cache(doctype="Item")
	frappe.db.commit()

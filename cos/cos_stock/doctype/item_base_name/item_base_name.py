# Copyright (c) 2025, BIoT and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class ItemBaseName(NestedSet):
	pass


@frappe.whitelist()
def set_abbreviation(name, abbreviation):
	"""按行设置单条 Item Base Name 的缩写。供 REST/MCP 按行修改。"""
	if not name or not abbreviation:
		frappe.throw(frappe._("name 与 abbreviation 必填"))
	if not frappe.db.exists("Item Base Name", name):
		frappe.throw(frappe._("Item Base Name 不存在: {0}").format(name))
	abbreviation = (abbreviation or "").strip()[:20]
	if not abbreviation:
		frappe.throw(frappe._("abbreviation 不能为空"))
	frappe.db.set_value("Item Base Name", name, "abbreviation", abbreviation, update_modified=True)
	frappe.db.commit()
	return {"ok": True, "name": name, "abbreviation": abbreviation}


@frappe.whitelist()
def get_abbreviation_plan():
	"""返回应在服务器上应用的缩写计划：[{name, base_name, abbreviation}, ...]，已做唯一性解析。供 REST 拉取后按行调用 set_abbreviation。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import (
		BASE_NAME_ABBREVIATION,
		_resolve_unique_abbreviations,
	)

	def _norm(s):
		return (s or "").strip()

	if not frappe.db.exists("DocType", "Item Base Name"):
		return []
	try:
		if not frappe.db.has_column("tabItem Base Name", "abbreviation"):
			return []
	except Exception:
		return []
	rows = frappe.get_all(
		"Item Base Name",
		filters={},
		fields=["name", "base_name", "abbreviation"],
	)
	key_to_rows = {}
	for r in rows:
		key = _norm(r.get("base_name"))
		if not key:
			continue
		key_to_rows.setdefault(key, []).append(r)
	rows_to_update = []
	for key in BASE_NAME_ABBREVIATION:
		if key not in key_to_rows:
			continue
		for r in key_to_rows[key]:
			rows_to_update.append(r)
	updating_names = {r["name"] for r in rows_to_update}
	existing_abbreviations = {
		r["abbreviation"] for r in rows
		if r.get("abbreviation") and r["name"] not in updating_names
	}
	if not rows_to_update:
		return []
	docname_to_abbr = _resolve_unique_abbreviations(rows_to_update, existing_abbreviations)
	return [
		{"name": docname, "base_name": next(r["base_name"] for r in rows_to_update if r["name"] == docname), "abbreviation": abbr}
		for docname, abbr in docname_to_abbr.items()
	]


@frappe.whitelist()
def fill_empty_abbreviations():
	"""为缩写为空的基础名按映射补填缩写（英文优先+唯一性）。返回更新条数。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import run_fill_abbreviations

	return run_fill_abbreviations()

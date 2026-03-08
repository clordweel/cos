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
	"""返回应在服务器上应用的缩写计划：[{name, base_name, abbreviation}, ...]，已做唯一性解析。映射从 UTF-8 JSON 加载。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import (
		_get_mapping,
		_resolve_unique_abbreviations,
	)

	def _norm(s):
		return (s or "").strip()

	if not frappe.db.exists("DocType", "Item Base Name"):
		return []
	mapping = _get_mapping()
	try:
		rows = frappe.get_all(
		"Item Base Name",
		filters={},
		fields=["name", "base_name", "abbreviation"],
	)
	except Exception:
		return []
	key_to_rows = {}
	for r in rows:
		key = _norm(r.get("base_name"))
		if not key:
			continue
		key_to_rows.setdefault(key, []).append(r)
	rows_to_update = []
	for key in mapping:
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
	docname_to_abbr = _resolve_unique_abbreviations(rows_to_update, existing_abbreviations, mapping)
	return [
		{"name": docname, "base_name": next(r["base_name"] for r in rows_to_update if r["name"] == docname), "abbreviation": abbr}
		for docname, abbr in docname_to_abbr.items()
	]


@frappe.whitelist()
def get_abbreviation_diagnostic():
	"""诊断缩写不生效：返回 has_column、row_count、match_count、mapping_source、样本 key 等，便于查编码/匹配问题。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import _get_mapping, _normalize_base_name

	out = {"has_doctype": bool(frappe.db.exists("DocType", "Item Base Name"))}
	try:
		rows = frappe.get_all(
			"Item Base Name",
			filters={},
			fields=["name", "base_name", "abbreviation"],
		)
		out["has_column"] = True
	except Exception as e:
		out["has_column"] = False
		out["has_column_error"] = str(e)
		return out
	mapping = _get_mapping()
	out["row_count"] = len(rows)
	out["mapping_size"] = len(mapping)
	# 用 DB 的 base_name 去映射里查，统计能匹配上的条数
	match_count = 0
	for r in rows:
		key = _normalize_base_name(r.get("base_name"))
		if key and key in mapping:
			match_count += 1
	out["match_count"] = match_count
	# 映射来源：是否从 JSON 加载
	try:
		from pathlib import Path
		# .../cos/cos_stock/doctype/item_base_name/item_base_name.py -> parents[3] = cos 包根
		path = Path(__file__).resolve().parents[3] / "patches" / "v1_2" / "item_base_name_abbreviations.json"
		out["mapping_source"] = "json" if path.exists() else "fallback"
	except Exception:
		out["mapping_source"] = "unknown"
	# 样本：第一条 DB 的 base_name 与映射中第一个 key 的 repr（便于看编码）
	if rows:
		out["sample_db_key"] = repr(rows[0].get("base_name"))
	if mapping:
		first_key = next(iter(mapping))
		out["sample_map_key"] = repr(first_key)
		out["sample_map_key_in_db_keys"] = first_key in [_normalize_base_name(r.get("base_name")) for r in rows]
	return out


@frappe.whitelist()
def fill_empty_abbreviations():
	"""为缩写为空的基础名按映射补填缩写（英文优先+唯一性）。返回更新条数。"""
	from cos.patches.v1_2.fill_item_base_name_abbreviations import run_fill_abbreviations

	return run_fill_abbreviations()

"""添加皮带机核心物料参数模板：压带轮、槽型托辊组、皮带输送机整机。"""
from __future__ import annotations

import frappe


def execute():
	for name, template_fn in [
		("标准模板 - 压带轮", _make_pressure_pulley_template),
		("标准模板 - 槽型托辊组", _make_trough_idler_set_template),
		("标准模板 - 皮带输送机", _make_belt_conveyor_template),
	]:
		if not frappe.db.exists("Item Parameter Template", name):
			doc = frappe.get_doc(template_fn())
			doc.insert(ignore_permissions=True)
			frappe.db.commit()


def _param(parameter_name: str, constraint_type: str, **kw) -> dict:
	"""构建参数行，补全默认字段。"""
	d = {
		"doctype": "Item Parameter Template Definition",
		"parameter_name": parameter_name,
		"constraint_type": constraint_type,
		"binding_field": kw.get("binding_field", 0),
		"join_to_hash": kw.get("join_to_hash", 0),
		"optional": kw.get("optional", 0),
		"readonly_value": kw.get("readonly_value", 0),
		"target_field": kw.get("target_field"),
		"parameter_default_value": kw.get("parameter_default_value"),
		"value_format": kw.get("value_format"),
		"doctype_selector": kw.get("doctype_selector"),
		"value_doctype": kw.get("value_doctype"),
		"value_integer": kw.get("value_integer"),
	}
	return {k: v for k, v in d.items() if v is not None}


def _make_pressure_pulley_template() -> dict:
	"""压带轮：直径、适配带宽，按个计。"""
	params = [
		_param("基础名", "Data", parameter_default_value="压带轮", join_to_hash=1),
		_param("直径D", "Integer", join_to_hash=1, parameter_default_value=""),
		_param("适配带宽", "Data", join_to_hash=1, parameter_default_value=""),
		_param("规格", "Format", value_format="Φ{{ 直径D or 0 }} [{{ 适配带宽 }}]", target_field="custom_specification", binding_field=1),
		_param("供应类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1, value_doctype="采购"),
		_param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1, value_doctype="Q235B"),
		_param("物料名称", "Format", value_format="{{ 基础名 }} Φ{{ 直径D or 0 }}{% if 适配带宽 %} {{ 适配带宽 }}{% endif %}", target_field="item_name", binding_field=1),
		_param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: Φ{{ 直径D or 0 }} | 适用: {{ 适配带宽 }} | 材质: {{ 材质 }}", target_field="description", binding_field=1),
		_param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="个", target_field="stock_uom", binding_field=1, value_doctype="个"),
		_param("库存属性", "Integer", parameter_default_value="1", target_field="is_stock_item", binding_field=1, value_integer=1, readonly_value=1),
	]
	return {
		"doctype": "Item Parameter Template",
		"name": "标准模板 - 压带轮",
		"template_name": "标准模板 - 压带轮",
		"item_group": "传动部件",
		"module": "COS Stock",
		"description": "适用于皮带机压带轮。核心参数：直径(mm)、适配带宽(如 B500)。",
		"parameters": params,
		"uoms": [{"uom": "个", "conversion_factor": 1.0}],
	}


def _make_trough_idler_set_template() -> dict:
	"""槽型托辊组：管径、辊长、轴径、适配带宽，按组计。每组通常 3 根。"""
	params = [
		_param("基础名", "Data", parameter_default_value="槽型托辊组", join_to_hash=1),
		_param("托辊类型", "Data", parameter_default_value="槽型上托辊", join_to_hash=1),
		_param("管径D", "Integer", join_to_hash=1, parameter_default_value=""),
		_param("辊长L", "Integer", join_to_hash=1, parameter_default_value=""),
		_param("轴径d", "Integer", join_to_hash=1, parameter_default_value=""),
		_param("适配带宽", "Data", join_to_hash=1, parameter_default_value=""),
		_param("每组根数", "Integer", parameter_default_value="3", join_to_hash=1),
		_param("规格", "Format", value_format="Φ{{ 管径D or 0 }}x{{ 辊长L or 0 }} (轴{{ 轴径d or 0 }}) x{{ 每组根数 or 3 }}{% if 适配带宽 %} [{{ 适配带宽 }}]{% endif %}", target_field="custom_specification", binding_field=1),
		_param("供应类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1, value_doctype="采购"),
		_param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1, value_doctype="Q235B"),
		_param("物料名称", "Format", value_format="{{ 基础名 }} Φ{{ 管径D or 0 }}x{{ 辊长L or 0 }}{% if 适配带宽 %} {{ 适配带宽 }}{% endif %}", target_field="item_name", binding_field=1),
		_param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: Φ{{ 管径D or 0 }}x{{ 辊长L or 0 }} (轴{{ 轴径d or 0 }}) | 每组{{ 每组根数 or 3 }}根 | 适用: {{ 适配带宽 }} | 材质: {{ 材质 }}", target_field="description", binding_field=1),
		_param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="组", target_field="stock_uom", binding_field=1, value_doctype="组"),
		_param("库存属性", "Integer", parameter_default_value="1", target_field="is_stock_item", binding_field=1, value_integer=1, readonly_value=1),
	]
	return {
		"doctype": "Item Parameter Template",
		"name": "标准模板 - 槽型托辊组",
		"template_name": "标准模板 - 槽型托辊组",
		"item_group": "传动部件",
		"module": "COS Stock",
		"description": "适用于皮带机槽型托辊组。核心尺寸：管径 x 辊长。每组通常 3 根。",
		"parameters": params,
		"uoms": [{"uom": "组", "conversion_factor": 1.0}, {"uom": "根", "conversion_factor": 0.0}],
	}


def _make_belt_conveyor_template() -> dict:
	"""皮带输送机整机：非库存，按台。带宽、长度可选。"""
	params = [
		_param("基础名", "Data", parameter_default_value="皮带输送机", join_to_hash=1),
		_param("带宽B", "Integer", join_to_hash=1, parameter_default_value=""),
		_param("规格", "Format", value_format="B{{ 带宽B or 0 }}", target_field="custom_specification", binding_field=1),
		_param("供应类型", "Doctype", doctype_selector="Source Type", parameter_default_value="自制", target_field="custom_source_type", binding_field=1, value_doctype="自制"),
		_param("物料名称", "Format", value_format="{{ 基础名 }} B{{ 带宽B or 0 }}", target_field="item_name", binding_field=1),
		_param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: B{{ 带宽B or 0 }} || 供应: {{ 供应类型 }}", target_field="description", binding_field=1),
		_param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="台", target_field="stock_uom", binding_field=1, value_doctype="台"),
		_param("库存属性", "Integer", parameter_default_value="0", target_field="is_stock_item", binding_field=1, value_integer=0, readonly_value=1),
	]
	return {
		"doctype": "Item Parameter Template",
		"name": "标准模板 - 皮带输送机",
		"template_name": "标准模板 - 皮带输送机",
		"item_group": "产成品",
		"module": "COS Stock",
		"description": "皮带输送机整机（非库存）。按台交付。",
		"parameters": params,
		"uoms": [{"uom": "台", "conversion_factor": 1.0}],
	}

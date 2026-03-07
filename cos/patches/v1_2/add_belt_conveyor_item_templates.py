"""添加皮带输送机采购单缺漏物料参数模板：半圆头螺栓、T型螺母、T型螺丝杆、封边型材。"""
from __future__ import annotations

import frappe


def execute():
    for name, template_fn in [
        ("标准模板 - 半圆头螺栓", _make_round_bolt_template),
        ("标准模板 - T型螺母", _make_t_nut_template),
        ("标准模板 - T型螺丝杆", _make_t_rod_template),
        ("标准模板 - 封边型材", _make_edge_profile_template),
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
    }
    return {k: v for k, v in d.items() if v is not None}


def _make_round_bolt_template() -> dict:
    """半圆头螺栓：结构同六角螺栓，基础名 半圆头螺栓。"""
    params = [
        _param("基础名", "Data", parameter_default_value="半圆头螺栓", join_to_hash=1, binding_field=0),
        _param("来源类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1),
        _param("公称直径", "Float", join_to_hash=1),
        _param("长度", "Float", join_to_hash=1),
        _param("牙距", "Float", optional=1),
        _param("强度等级", "Data", parameter_default_value="8.8", join_to_hash=1),
        _param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1),
        _param("表面处理", "Doctype", doctype_selector="Item Surface", parameter_default_value="发黑", target_field="custom_surface_treatment", join_to_hash=1, binding_field=1),
        _param("执行标准", "Doctype", doctype_selector="Executive Standard", parameter_default_value="GB/T 5783", optional=1, target_field="custom_tech_standard_number", join_to_hash=1, binding_field=1),
        _param("规格型号", "Format", value_format="M{{ 公称直径 or 0 }}x{{ 长度 or 0 }}{% if 牙距 %}x{{ 牙距 }}{% endif %}", target_field="custom_specification", binding_field=1),
        _param("物料名称", "Format", value_format="{{ 基础名 }} {{ 规格型号 }} {{ 强度等级 }} {{ 表面处理 }}{% if 材质 and 材质 != 'Q235B' %} {{ 材质 }}{% endif %}", target_field="item_name", binding_field=1),
        _param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: {{ 规格型号 }} | 等级: {{ 强度等级 }} | 表面: {{ 表面处理 }} | 材质: {{ 材质 }}{% if 执行标准 %} | 标准: {{ 执行标准 }}{% endif %}", target_field="description", binding_field=1),
        _param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="个", target_field="stock_uom", binding_field=1, value_doctype="个"),
    ]
    return {
        "doctype": "Item Parameter Template",
        "name": "标准模板 - 半圆头螺栓",
        "template_name": "标准模板 - 半圆头螺栓",
        "item_group": "紧固件",
        "module": "COS Stock",
        "description": "专用于半圆头螺栓。规格与六角螺栓相同。",
        "parameters": params,
        "uoms": [{"uom": "个", "conversion_factor": 1.0}, {"uom": "千克", "conversion_factor": 0.0}],
    }


def _make_t_nut_template() -> dict:
    """T型螺母：规格 T30 等。"""
    params = [
        _param("基础名", "Data", parameter_default_value="T型螺母", join_to_hash=1),
        _param("规格型号", "Data", join_to_hash=1),
        _param("规格", "Format", value_format="{{ 规格型号 }}", target_field="custom_specification", binding_field=1),
        _param("来源类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1),
        _param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1),
        _param("物料名称", "Format", value_format="{{ 基础名 }} {{ 规格 }}", target_field="item_name", binding_field=1),
        _param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}", target_field="description", binding_field=1),
        _param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="个", target_field="stock_uom", binding_field=1, value_doctype="个"),
    ]
    return {
        "doctype": "Item Parameter Template",
        "name": "标准模板 - T型螺母",
        "template_name": "标准模板 - T型螺母",
        "item_group": "紧固件",
        "module": "COS Stock",
        "description": "适用于 T 型螺纹螺母，如 T30。",
        "parameters": params,
        "uoms": [{"uom": "个", "conversion_factor": 1.0}],
    }


def _make_t_rod_template() -> dict:
    """T型螺丝杆：规格 T30x6（规格代号×螺距），按米计。"""
    params = [
        _param("基础名", "Data", parameter_default_value="T型丝杆", join_to_hash=1),
        _param("规格型号", "Data", join_to_hash=1),
        _param("规格", "Format", value_format="{{ 规格型号|replace('*','x')|replace('-','x') }}", target_field="custom_specification", binding_field=1),
        _param("来源类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1),
        _param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1),
        _param("物料名称", "Format", value_format="{{ 基础名 }} {{ 规格 }}", target_field="item_name", binding_field=1),
        _param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}", target_field="description", binding_field=1),
        _param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="米", target_field="stock_uom", binding_field=1, value_doctype="米"),
    ]
    return {
        "doctype": "Item Parameter Template",
        "name": "标准模板 - T型螺丝杆",
        "template_name": "标准模板 - T型螺丝杆",
        "item_group": "型材",
        "module": "COS Stock",
        "description": "适用于 T 型螺纹丝杆，规格如 T30x6（规格代号×螺距），按米计。",
        "parameters": params,
        "uoms": [{"uom": "米", "conversion_factor": 1.0}],
    }


def _make_edge_profile_template() -> dict:
    """封边型材：厚度×宽度，如 10×200，按米计。编码 EDGE-厚度x宽度。"""
    params = [
        _param("基础名", "Data", parameter_default_value="封边胶带", join_to_hash=1),
        _param("厚度", "Float", join_to_hash=1),
        _param("宽度", "Float", join_to_hash=1),
        _param("规格", "Format", value_format="{{ 厚度 or 0 }}×{{ 宽度 or 0 }}", target_field="custom_specification", binding_field=1),
        _param("来源类型", "Doctype", doctype_selector="Source Type", parameter_default_value="采购", target_field="custom_source_type", binding_field=1),
        _param("材质", "Doctype", doctype_selector="Item Material", parameter_default_value="Q235B", target_field="custom_body_material", join_to_hash=1, binding_field=1),
        _param("物料名称", "Format", value_format="{{ 基础名 }} {{ 规格 }}", target_field="item_name", binding_field=1),
        _param("详细描述", "Format", value_format="产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}", target_field="description", binding_field=1),
        _param("计量单位", "Doctype", doctype_selector="UOM", parameter_default_value="米", target_field="stock_uom", binding_field=1, value_doctype="米"),
    ]
    return {
        "doctype": "Item Parameter Template",
        "name": "标准模板 - 封边型材",
        "template_name": "标准模板 - 封边型材",
        "item_group": "型材",
        "module": "COS Stock",
        "description": "适用于封边胶带/角钢件等，规格为厚度×宽度（如 10×200），编码 EDGE-厚度x宽度，按米计。",
        "parameters": params,
        "uoms": [{"uom": "米", "conversion_factor": 1.0}],
    }

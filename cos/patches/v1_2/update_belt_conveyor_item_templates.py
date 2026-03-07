"""更新皮带输送机物料参数模板：T型丝杆规格 T30x6、封边型材规范编码/名称/规格。"""
from __future__ import annotations

import frappe


def execute():
    _update_t_nut_template()
    _update_t_rod_template()
    _update_edge_profile_template()


def _update_t_nut_template():
    """T型螺母：补规格 Format 绑定 custom_specification。"""
    name = "标准模板 - T型螺母"
    if not frappe.db.exists("Item Parameter Template", name):
        return
    doc = frappe.get_doc("Item Parameter Template", name)
    param_names = [p.parameter_name for p in doc.parameters]

    if "规格" not in param_names:
        doc.append(
            "parameters",
            {
                "parameter_name": "规格",
                "constraint_type": "Format",
                "parameter_default_value": "{{ 规格型号 }}",
                "value_format": "{{ 规格型号 }}",
                "target_field": "custom_specification",
                "binding_field": 1,
            },
        )

    for p in doc.parameters:
        if p.parameter_name == "物料名称":
            p.value_format = "{{ 基础名 }} {{ 规格 }}"
            p.parameter_default_value = p.value_format
        elif p.parameter_name == "详细描述":
            p.value_format = "产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}"
            p.parameter_default_value = p.value_format

    doc.save(ignore_permissions=True)
    frappe.db.commit()


def _update_t_rod_template():
    """T型丝杆：补规格 Format（T30x6），物料名称/详细描述引用规格。"""
    name = "标准模板 - T型螺丝杆"
    if not frappe.db.exists("Item Parameter Template", name):
        return
    doc = frappe.get_doc("Item Parameter Template", name)
    param_names = [p.parameter_name for p in doc.parameters]

    if "规格" not in param_names:
        doc.append(
            "parameters",
            {
                "parameter_name": "规格",
                "constraint_type": "Format",
                "parameter_default_value": "{{ 规格型号|replace('*','x')|replace('-','x') }}",
                "value_format": "{{ 规格型号|replace('*','x')|replace('-','x') }}",
                "target_field": "custom_specification",
                "binding_field": 1,
            },
        )

    for p in doc.parameters:
        if p.parameter_name == "物料名称":
            p.value_format = "{{ 基础名 }} {{ 规格 }}"
            p.parameter_default_value = p.value_format
        elif p.parameter_name == "详细描述":
            p.value_format = "产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}"
            p.parameter_default_value = p.value_format

    doc.save(ignore_permissions=True)
    frappe.db.commit()


def _update_edge_profile_template():
    """封边型材：改为厚度×宽度参数，规范编码 EDGE-厚度x宽度、名称、规格。"""
    name = "标准模板 - 封边型材"
    if not frappe.db.exists("Item Parameter Template", name):
        return
    doc = frappe.get_doc("Item Parameter Template", name)
    param_names = [p.parameter_name for p in doc.parameters]

    if "截面规格" in param_names and "厚度" not in param_names:
        for i in range(len(doc.parameters) - 1, -1, -1):
            if doc.parameters[i].parameter_name == "截面规格":
                doc.remove(doc.parameters[i])
                break

        for row in [
            {"parameter_name": "厚度", "constraint_type": "Float", "join_to_hash": 1},
            {"parameter_name": "宽度", "constraint_type": "Float", "join_to_hash": 1},
            {
                "parameter_name": "规格",
                "constraint_type": "Format",
                "value_format": "{{ 厚度 or 0 }}×{{ 宽度 or 0 }}",
                "parameter_default_value": "{{ 厚度 or 0 }}×{{ 宽度 or 0 }}",
                "target_field": "custom_specification",
                "binding_field": 1,
            },
        ]:
            doc.append("parameters", row)

        for p in doc.parameters:
            if p.parameter_name == "物料名称":
                p.value_format = "{{ 基础名 }} {{ 规格 }}"
                p.parameter_default_value = p.value_format
            elif p.parameter_name == "详细描述":
                p.value_format = "产品: {{ 基础名 }} | 规格: {{ 规格 }} | 材质: {{ 材质 }}"
                p.parameter_default_value = p.value_format

        doc.description = "适用于封边胶带/角钢件等，规格为厚度×宽度（如 10×200），编码 EDGE-厚度x宽度，按米计。"
        doc.save(ignore_permissions=True)
        frappe.db.commit()

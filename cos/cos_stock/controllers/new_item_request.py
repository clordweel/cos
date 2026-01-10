# Copyright (c) 2025, BIoT and contributors
# For license information, please see license.txt

import json
import re
import html
import frappe
from frappe.utils import flt


@frappe.whitelist()
def check_duplicate_request(unique_code, current_docname=None):
	"""检查是否存在相同参数指纹的已提交申请（独立函数，避免文档状态检查）"""
	if not unique_code:
		return {"duplicate": False, "message": "指纹为空，无法检查重复。"}

	filters = {
		"docstatus": 1,
		"unique_code": unique_code,
	}
	if current_docname:
		filters["name"] = ["!=", current_docname]
	
	duplicate_name = frappe.db.get_value(
		"New Item Request",
		filters=filters,
		fieldname="name",
		order_by="modified DESC",
	)

	if duplicate_name:
		return {
			"duplicate": True,
			"name": duplicate_name,
			"message": f"发现重复的参数组合！重复文档：{duplicate_name}。",
		}
	return {"duplicate": False, "message": "没有发现重复的参数组合。"}


@frappe.whitelist()
def get_binding_fields_from_request(item_name):
	"""从关联的物料申请单获取绑定字段数据，仅返回绑定字段"""
	if not item_name:
		frappe.throw("物料名称是必需的。")
	
	# 获取 Item 文档
	item = frappe.get_doc("Item", item_name)
	
	# 检查是否有关联的物料申请单
	if not item.custom_new_item_request:
		frappe.throw("此物料未关联到物料申请单。")
	
	# 获取物料申请单文档
	request_doc = frappe.get_doc("New Item Request", item.custom_new_item_request)
	
	# 允许 Administrator 在草稿模式下执行，其他用户只能在已提交状态下执行
	if request_doc.docstatus != 1:
		if frappe.session.user != "Administrator":
			frappe.throw("此操作只能在已提交的物料申请单上执行。")
	
	# 顺序处理参数，构建最终 Context
	final_context = {}
	assignment_rules = []
	sorted_parameters = sorted(request_doc.parameters, key=lambda x: x.idx)
	
	for row in sorted_parameters:
		p_name = row.parameter_name
		if row.constraint_type != "Format":
			final_context[p_name] = row.parameter_value
		else:
			template_str = (
				row.parameter_value or row.value_format or row.parameter_default_value
			)
			if template_str:
				try:
					rendered = frappe.render_template(
						html.unescape(template_str), final_context
					)
					rendered = re.sub(r"\s+", " ", rendered).strip()
					final_context[p_name] = rendered
				except:
					final_context[p_name] = ""
		
		# 收集需要绑定到 Item 字段的规则（只收集绑定字段）
		if row.binding_field == 1 and row.target_field:
			assignment_rules.append(
				{"target_field": row.target_field, "parameter_name": p_name}
			)
	
	# 只返回绑定字段的数据
	binding_fields = {}
	for rule in assignment_rules:
		val = final_context.get(rule["parameter_name"])
		if val is not None:
			binding_fields[rule["target_field"]] = val
	
	return {
		"binding_fields": binding_fields,
		"request_name": request_doc.name,
		"fields_count": len(binding_fields)
	}

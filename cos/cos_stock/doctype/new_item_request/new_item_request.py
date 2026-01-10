# Copyright (c) 2025, BIoT and contributors
# For license information, please see license.txt

import json
import re
import html
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class NewItemRequest(Document):

	@frappe.whitelist()
	def preview_parameters(self, parameters=None, context=None):
		"""前端预览计算逻辑：支持级联引用"""
		# 如果没有传入 parameters，使用当前文档的参数
		if parameters is None:
			parameters = self.parameters
		if isinstance(parameters, str):
			parameters = json.loads(parameters)
		if isinstance(context, str):
			context = json.loads(context)

		# 1. 整理初始上下文，处理数值类型
		safe_context = {}
		if context:
			for k, v in context.items():
				if v is None or v == "":
					safe_context[k] = ""
					continue
				try:
					f_val = float(v)
					safe_context[k] = int(f_val) if f_val.is_integer() else f_val
				except ValueError:
					safe_context[k] = v

		# 2. 核心：按 idx 排序，确保级联计算顺序
		sorted_params = sorted(parameters, key=lambda x: x.get("idx", 0))
		result = {}

		for row in sorted_params:
			p_name = row.get("parameter_name")
			if row.get("constraint_type") == "Format":
				raw_template = row.get("value_format") or row.get("parameter_default_value")
				if not raw_template:
					continue

				try:
					# 反转义 HTML (处理 > < 等符号) 并渲染
					template = html.unescape(raw_template)
					rendered_value = frappe.render_template(template, safe_context)

					# 清理多余空格和换行
					rendered_value = re.sub(r"\n\s*\n", "\n", rendered_value).strip()
					rendered_value = re.sub(r" +", " ", rendered_value)

					result[row.get("name")] = rendered_value

					# 🌟 关键：将当前渲染结果存入上下文，供后续 Format 行引用
					if p_name:
						safe_context[p_name] = rendered_value
				except Exception as e:
					result[row.get("name")] = f"Rendering error: {str(e)}"
			else:
				# 非 Format 类型，确保上下文中的值是最新的
				if p_name:
					val = row.get("parameter_value")
					try:
						if val and str(val).replace(".", "", 1).isdigit():
							f_val = float(val)
							safe_context[p_name] = (
								int(f_val) if f_val.is_integer() else f_val
							)
						else:
							safe_context[p_name] = val
					except:
						safe_context[p_name] = val

		return result

	@frappe.whitelist()
	def generate_item_data_dict(self):
		"""正式生成 Item 数据字典：支持级联引用"""
		# 使用当前文档实例
		doc = self

		# 允许 Administrator 在草稿模式下执行，其他用户只能在已提交状态下执行
		if doc.docstatus != 1:
			if frappe.session.user != "Administrator":
				frappe.throw("This operation can only be performed on submitted documents.")

		# 1. 收集 UOM
		unit_conversions = []
		for row in doc.uoms or []:
			if not row or not hasattr(row, 'uom'):
				continue
			unit_conversions.append(
				{
					"doctype": "Item Unit Conversion",
					"uom": getattr(row, 'uom', None),
					"conversion_factor": flt(getattr(row, 'conversion_factor', 1)),
				}
			)

		# 2. 顺序处理参数，构建最终 Context
		final_context = {}
		assignment_rules = []
		# 过滤掉 None 值，并安全排序
		parameters_list = [row for row in (doc.parameters or []) if row is not None]
		sorted_parameters = sorted(parameters_list, key=lambda x: getattr(x, 'idx', 0) or 0)

		for row in sorted_parameters:
			if not row or not hasattr(row, 'parameter_name'):
				continue
				
			p_name = getattr(row, 'parameter_name', None)
			if not p_name:
				continue
				
			constraint_type = getattr(row, 'constraint_type', None)
			if constraint_type != "Format":
				parameter_value = getattr(row, 'parameter_value', None)
				final_context[p_name] = parameter_value
			else:
				template_str = (
					getattr(row, 'parameter_value', None) or 
					getattr(row, 'value_format', None) or 
					getattr(row, 'parameter_default_value', None)
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

			# 收集需要绑定到 Item 字段的规则
			binding_field = getattr(row, 'binding_field', 0)
			target_field = getattr(row, 'target_field', None)
			if binding_field == 1 and target_field:
				assignment_rules.append(
					{"target_field": target_field, "parameter_name": p_name}
				)

		# 3. 映射到 Item 字段
		item_fields = {
			"doctype": "Item",
			"is_stock_item": 1,
			"item_group": doc.item_group,
			"image": doc.image,
			"custom_new_item_request": doc.name,
			"custom_unique_code": doc.unique_code,
			"uoms": unit_conversions,
		}

		for rule in assignment_rules:
			val = final_context.get(rule["parameter_name"])
			if val is not None:
				item_fields[rule["target_field"]] = val

		return item_fields

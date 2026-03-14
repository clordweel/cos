# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""用户快捷创建员工相关工具。"""

import frappe
from frappe import _


@frappe.whitelist()
def get_employee_create_defaults():
	"""获取快捷创建员工时的默认值（公司、性别、入职日期等）。"""
	if not frappe.has_permission("Employee", "create"):
		frappe.throw(_("无权限创建员工"), frappe.PermissionError)

	defaults = {}
	# 默认公司
	defaults["company"] = frappe.defaults.get_user_default("company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	# 若仍无，取第一个公司
	if not defaults["company"]:
		company = frappe.db.get_value("Company", {"enabled": 1}, "name", order_by="creation asc")
		defaults["company"] = company

	# 默认性别（取第一个 Gender）
	defaults["gender"] = frappe.db.get_value("Gender", {}, "name", order_by="creation asc")

	# 入职日期默认今天
	defaults["date_of_joining"] = frappe.utils.today()

	# 出生日期占位（必填，用户可修改）
	defaults["date_of_birth"] = "1990-01-01"

	return defaults


@frappe.whitelist()
def get_employee_for_user(user):
	"""获取已关联该用户的员工名称，若无则返回 None。"""
	if not user:
		return None
	return frappe.db.get_value("Employee", {"user_id": user}, "name")

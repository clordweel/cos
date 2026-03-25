# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""同站点多公司：列出当前用户可访问的 Company、读取/设置会话默认公司（User Default `company`）。"""

import frappe
from frappe import _


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.AuthenticationError)


@frappe.whitelist()
def get_session_company():
	"""返回当前用户默认公司（ERPNext 会话公司）。"""
	_require_login()
	d = frappe.defaults.get_user_default("company", user=frappe.session.user)
	if not d:
		return {"company": None, "company_name": None}
	cname = frappe.db.get_value("Company", d, "company_name")
	return {"company": d, "company_name": cname}


@frappe.whitelist()
def list_accessible_companies():
	"""列出当前用户有读权限且未禁用的公司（受 User Permission 等约束）。"""
	_require_login()
	return frappe.get_list(
		"Company",
		filters={"disabled": 0},
		fields=["name", "company_name"],
		order_by="name",
		limit_page_length=0,
	)


@frappe.whitelist(methods=["POST"])
def set_default_company(company=None):
	"""设置当前用户默认公司；后续 Frappe / ERPNext API 按此公司上下文执行。"""
	_require_login()
	company = (company or "").strip()
	if not company:
		frappe.throw(_("Company is required"), frappe.ValidationError)
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company not found"), frappe.DoesNotExistError)
	if frappe.db.get_value("Company", company, "disabled"):
		frappe.throw(_("Company is disabled"), frappe.ValidationError)
	allowed = frappe.get_list(
		"Company",
		filters={"name": company, "disabled": 0},
		fields=["name"],
		limit_page_length=1,
	)
	if not allowed:
		frappe.throw(_("No permission for this company"), frappe.PermissionError)
	frappe.defaults.set_user_default("company", company, user=frappe.session.user)
	cname = frappe.db.get_value("Company", company, "company_name")
	return {"company": company, "company_name": cname}

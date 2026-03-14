# Copyright (c) 2026, COS and contributors
# For license information, please see license.txt

"""COS Accounts 自定义查询"""

import frappe
from frappe.desk.reportview import get_filters_cond, get_match_cond
from erpnext.controllers.queries import employee_query, get_fields


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def advance_employee_query(
	doctype,
	txt,
	searchfield,
	start,
	page_len,
	filters,
	reference_doctype: str | None = None,
	ignore_user_permissions: bool = False,
	*,
	link_fieldname: str | None = None,
):
	"""垫付员工选择：强制忽略 User Permission，使采购经理等可选取任意员工。

	仅当 reference_doctype 为 Purchase Order / Purchase Invoice 且
	link_fieldname 为 custom_advance_employee 时，直接执行查询并忽略 User Permission；
	否则回退到标准 employee_query。
	"""
	is_advance_field = (
		reference_doctype in ("Purchase Order", "Purchase Invoice")
		and link_fieldname == "custom_advance_employee"
	)

	if is_advance_field:
		# 垫付场景：采购经理等可能无 Employee 权限，直接查所有在职员工
		doctype = "Employee"
		conditions = []
		fields = get_fields(doctype, ["name", "employee_name"])
		search_conditions = " or ".join([f"{field} like %(txt)s" for field in fields])
		mcond = ""  # 不应用 User Permission 过滤

		return frappe.db.sql(
			"""select {fields} from `tabEmployee`
			where status in ('Active', 'Suspended')
				and docstatus < 2
				and ({key} like %(txt)s or {search_conditions})
				{fcond} {mcond}
			order by
				(case when locate(%(_txt)s, name) > 0 then locate(%(_txt)s, name) else 99999 end),
				(case when locate(%(_txt)s, employee_name) > 0 then locate(%(_txt)s, employee_name) else 99999 end),
				idx desc,
				name, employee_name
			limit %(page_len)s offset %(start)s""".format(
				**{
					"fields": ", ".join(fields),
					"key": searchfield,
					"fcond": get_filters_cond(doctype, filters, conditions),
					"mcond": mcond,
					"search_conditions": search_conditions,
				}
			),
			{"txt": "%%%s%%" % txt, "_txt": txt.replace("%", ""), "start": start, "page_len": page_len},
		)

	# 非垫付字段：回退到标准 employee_query
	return employee_query(
		doctype,
		txt,
		searchfield,
		start,
		page_len,
		filters,
		reference_doctype=reference_doctype,
		ignore_user_permissions=ignore_user_permissions,
	)

# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE
"""回填 PI 的 custom_employee_reimbursed：根据已提交的付给员工 PE 判断是否已报销。

用法:
  bench --site <site> execute cos.scripts.backfill_employee_reimbursed.run
"""
from __future__ import annotations

import frappe


def run():
	"""回填所有有 custom_payable_transfer_je 的 PI 的 custom_employee_reimbursed。"""
	pi_list = frappe.get_all(
		"Purchase Invoice",
		filters={
			"docstatus": 1,
			"custom_payable_transfer_je": ["!=", ""],
		},
		fields=["name", "custom_payable_transfer_je"],
	)
	updated = 0
	for pi in pi_list:
		je_name = pi.custom_payable_transfer_je
		if not je_name:
			continue
		reimbursed = _has_submitted_pe_for_je(je_name)
		status = "已报销" if reimbursed else "未报销"
		current = frappe.db.get_value("Purchase Invoice", pi.name, "custom_employee_reimbursed")
		# 兼容旧 0/1 值，或需更新为正确状态
		if current not in ("未报销", "已报销") or status != current:
			frappe.db.set_value(
				"Purchase Invoice",
				pi.name,
				"custom_employee_reimbursed",
				status,
				update_modified=False,
			)
			updated += 1
	frappe.db.commit()
	print(f"回填完成：检查 {len(pi_list)} 条 PI，更新 {updated} 条")
	return updated


def _has_submitted_pe_for_je(je_name: str) -> bool:
	"""是否存在已提交的 PE 引用该 JE。"""
	refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"reference_doctype": "Journal Entry",
			"reference_name": je_name,
		},
		fields=["parent"],
		pluck="parent",
	)
	for pe_name in set(refs):
		if frappe.db.get_value("Payment Entry", pe_name, "docstatus") == 1:
			return True
	return False

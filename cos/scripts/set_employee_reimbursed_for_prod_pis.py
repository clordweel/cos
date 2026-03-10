# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE
"""prod 迁移后：将指定员工垫付 PI 的 custom_employee_reimbursed 设为「未报销」。

仅更新 custom_is_employee_advance=1 的 PI；有 custom_payable_transfer_je 的按付给员工 PE 判断。

用法:
  bench --site junhai.local execute cos.scripts.set_employee_reimbursed_for_prod_pis.run
  bench --site junhai.local execute cos.scripts.set_employee_reimbursed_for_prod_pis.run --names "JMI-PINV-2600001,JMI-PINV-2600002,JMI-PINV-2600003,JMI-PINV-2600004"
"""
from __future__ import annotations

import frappe


DEFAULT_NAMES = [
	"JMI-PINV-2600001",
	"JMI-PINV-2600002",
	"JMI-PINV-2600003",
	"JMI-PINV-2600004",
]


def run(names: str | None = None):
	"""将指定 PI（员工垫付）的 custom_employee_reimbursed 设为正确状态。"""
	pi_names = (names or "").strip().split(",") if names else DEFAULT_NAMES
	pi_names = [n.strip() for n in pi_names if n.strip()]
	if not pi_names:
		print("未指定 PI 名称")
		return 0

	from cos.scripts.backfill_employee_reimbursed import _has_submitted_pe_for_je

	updated = 0
	for name in pi_names:
		if not frappe.db.exists("Purchase Invoice", name):
			print(f"跳过（不存在）: {name}")
			continue
		is_advance = frappe.db.get_value("Purchase Invoice", name, "custom_is_employee_advance")
		if not is_advance:
			print(f"跳过（非员工垫付）: {name}")
			continue
		je_name = frappe.db.get_value("Purchase Invoice", name, "custom_payable_transfer_je")
		if je_name:
			reimbursed = _has_submitted_pe_for_je(je_name)
			status = "已报销" if reimbursed else "未报销"
		else:
			status = "未报销"
		current = frappe.db.get_value("Purchase Invoice", name, "custom_employee_reimbursed")
		if current != status:
			frappe.db.set_value(
				"Purchase Invoice",
				name,
				"custom_employee_reimbursed",
				status,
				update_modified=False,
			)
			updated += 1
			print(f"更新: {name} -> {status}")
		else:
			print(f"无需更新: {name} ({status})")
	frappe.db.commit()
	print(f"完成：检查 {len(pi_names)} 条，更新 {updated} 条")
	return updated

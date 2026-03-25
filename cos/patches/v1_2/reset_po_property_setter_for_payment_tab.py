"""解除 Customize Form 对采购订单字段顺序的锁定，使「付款」Tab 等 Custom Field 按 insert_after 合并进表单。

根因：Desk「自定义表单」保存后会产生 Property Setter「field_order」（如 Purchase Order-main-field_order），
其 JSON 若在新增 Tab Break 之前生成，不会包含 custom_tab_payment，Frappe 将严格按该顺序渲染，
导致后续新增的「付款」Tab 永远不出现。

本 patch 幂等：
1. 删除 Purchase Order 主表单的 field_order Property Setter；
2. 删除挂在这四个自定义字段上的 Property Setter（避免 hidden 等覆盖）；
3. 再次执行 ensure_po_payment_tab 以校正锚点与 Section 挂载。
"""

from __future__ import annotations

import importlib

import frappe

_PAYMENT_CHAIN_FIELDS = (
	"custom_tab_payment",
	"custom_section_employee_advance_reimbursement",
	"custom_is_employee_advance",
	"custom_advance_employee",
)


def execute():
	# 1) 主表单 field_order（Customize Form 保存的布局快照）
	frappe.db.sql(
		"""
		DELETE FROM `tabProperty Setter`
		WHERE doc_type = 'Purchase Order'
		  AND property = 'field_order'
		  AND doctype_or_field = 'DocType'
		  AND IFNULL(field_name, '') = ''
		"""
	)

	# 2) 对「付款」链上字段的任意 Property Setter（hidden、label、collapsible 等）
	ph = ", ".join(["%s"] * len(_PAYMENT_CHAIN_FIELDS))
	frappe.db.sql(
		f"""
		DELETE FROM `tabProperty Setter`
		WHERE doc_type = 'Purchase Order'
		  AND field_name IN ({ph})
		""",
		tuple(_PAYMENT_CHAIN_FIELDS),
	)

	importlib.import_module("cos.patches.v1_2.ensure_po_payment_tab").execute()

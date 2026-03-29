# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""工作台 / 库存调账列表：壳顶栏改为 app_bar 并显示标题；desk_home 入口与 v16 /app 根路径对齐。"""

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabCOS Work Mini Program`
		SET nav_bar_inset_mode = 'app_bar',
			show_nav_bar_title = 1
		WHERE name IN ('stock_reconciliation', 'desk_home')
		"""
	)

# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""COS Work Mini Program.nav_bar_inset_mode：status_bar → safe_area（与壳布局语义对齐）。"""

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabCOS Work Mini Program`
		SET nav_bar_inset_mode = 'safe_area'
		WHERE ifnull(nav_bar_inset_mode, '') IN ('status_bar', 'status_bar_only')
		"""
	)

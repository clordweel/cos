# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""COS Work Mini Program.nav_bar_inset_mode：旧选项迁移为 none / status_bar / app_bar。"""

import frappe


def execute():
	mapping = {
		"status_bar_only": "status_bar",
		"app_provided": "app_bar",
		"page_custom": "none",
	}
	rows = frappe.db.sql(
		"""
		SELECT name, nav_bar_inset_mode FROM `tabCOS Work Mini Program`
		WHERE ifnull(nav_bar_inset_mode, '') != ''
		""",
		as_dict=True,
	)
	for row in rows:
		old = (row.nav_bar_inset_mode or "").strip()
		new = mapping.get(old)
		if new:
			frappe.db.set_value(
				"COS Work Mini Program",
				row.name,
				"nav_bar_inset_mode",
				new,
				update_modified=False,
			)

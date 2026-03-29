# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class COSWorkMiniProgramRole(Document):
	def validate(self):
		if not (self.export_module or "").strip():
			self.export_module = "COS Share"
		existing = frappe.db.get_value(
			"COS Work Mini Program Role",
			{"role": self.role, "mini_program": self.mini_program},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(_("该角色已绑定此小程序，请勿重复添加"))

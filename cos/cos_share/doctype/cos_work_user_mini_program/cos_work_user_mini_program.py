# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class COSWorkUserMiniProgram(Document):
	def validate(self):
		if (
			frappe.session.user != "Administrator"
			and self.user
			and self.user != frappe.session.user
		):
			frappe.throw(_("只能为自己添加工作台小程序"))
		existing = frappe.db.get_value(
			"COS Work User Mini Program",
			{"user": self.user, "mini_program": self.mini_program},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(_("该用户已添加此小程序"))

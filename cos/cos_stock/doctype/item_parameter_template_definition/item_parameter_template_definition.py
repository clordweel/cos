# Copyright (c) 2025, BIoT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemParameterTemplateDefinition(Document):
	def validate(self):
		# 验证：如果 constraint_type 是 Doctype，必须先设置 doctype_selector 才能设置 value_doctype
		if self.constraint_type == 'Doctype':
			if self.value_doctype and not self.doctype_selector:
				frappe.throw(
					__('文档类型选择器必须首先设置。'),
					title=__('验证错误')
				)
		
		# 验证：如果 constraint_type 不是 Doctype，不应该有 value_doctype 和 doctype_selector
		if self.constraint_type != 'Doctype':
			if self.value_doctype:
				self.value_doctype = None
			if self.doctype_selector:
				self.doctype_selector = None

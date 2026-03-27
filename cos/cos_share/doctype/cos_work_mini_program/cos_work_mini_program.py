# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class COSWorkMiniProgram(Document):
	def validate(self):
		self._validate_launch_path()
		self._validate_icon_url()

	def _validate_launch_path(self):
		lp = (self.launch_path or "").strip()
		if not lp.startswith("/"):
			frappe.throw(_("入口路径必须以 / 开头"))
		if "://" in lp or ".." in lp or "\n" in lp or "\r" in lp:
			frappe.throw(_("入口路径不允许包含协议、换行或 .."))

	def _validate_icon_url(self):
		iu = (self.icon_url or "").strip()
		if not iu:
			return
		if iu.startswith("/"):
			return
		if iu.startswith("https://") or iu.startswith("http://"):
			return
		frappe.throw(_("图标 URL 须为 http(s) 完整链接或以 / 开头的站内路径"))

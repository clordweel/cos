# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


_URL_RE = re.compile(r"^https?://", re.I)


class CosWorkAppRelease(Document):
	def validate(self):
		self._validate_download_source()
		self._validate_unique_channel_build()
		self._validate_url()

	def _validate_download_source(self):
		if not (self.download_url or "").strip() and not (self.apk_file or "").strip():
			frappe.throw(_("请填写「下载链接」或上传「APK 附件」至少一项"))

	def _validate_unique_channel_build(self):
		existing = frappe.db.get_value(
			"Cos Work App Release",
			{"channel": self.channel, "build_number": self.build_number},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(
				_("同一分发渠道下构建号 {0} 已存在：{1}").format(self.build_number, existing)
			)

	def _validate_url(self):
		url = (self.download_url or "").strip()
		if not url:
			return
		if not _URL_RE.match(url):
			frappe.throw(_("下载链接须以 http:// 或 https:// 开头"))

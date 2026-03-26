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
		self._warn_name_channel_mismatch()

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

	def _warn_name_channel_mismatch(self):
		"""编号在首次保存后固定；若之后改「分发渠道」，编号中的渠道段会与字段不一致，易误解。"""
		name = (self.name or "").strip()
		if not name.startswith("CWAR-") or not self.channel:
			return
		parts = name.split("-")
		if len(parts) < 3:
			return
		segment = parts[1]
		if segment != self.channel:
			frappe.msgprint(
				_(
					"当前编号「{0}」中的渠道为「{1}」，与字段「分发渠道」（{2}）不一致。"
					"网站与 API 仅按「分发渠道」筛选；若需编号与之一致，请另存为新单据。"
				).format(name, segment, self.channel),
				title=_("渠道与编号不一致"),
				indicator="orange",
			)

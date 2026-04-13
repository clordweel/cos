# Copyright (c) 2026, COS and contributors
"""购销合同打印辅助：公章等资源。"""

from __future__ import annotations

import base64
import mimetypes
import os
from urllib.parse import urljoin

import frappe


def company_contract_seal_image_src(company: str | None) -> str:
	"""返回合同专用章在打印 HTML 中可用的 img src。

	优先使用 data URI，避免 PDF（Chrome headless）无法加载需 Cookie 的 /private/files URL。
	若读盘失败则退回站点绝对 URL（公开文件仍可能可用）。
	"""
	if not company:
		return ""
	path = frappe.db.get_value("Company", company, "custom_contract_seal_image")
	if not path:
		return ""
	path = str(path).strip()
	if not path:
		return ""

	file_name = frappe.db.get_value("File", {"file_url": path}, "name")
	if not file_name or not frappe.db.exists("File", file_name):
		return _absolute_url(path)

	fdoc = frappe.get_doc("File", file_name)
	fdoc.flags.ignore_permissions = True
	full = fdoc.get_full_path()

	if not full or not os.path.isfile(full):
		return _absolute_url(path)

	mime = mimetypes.guess_type(full)[0] or "image/png"
	try:
		with open(full, "rb") as fh:
			b64 = base64.b64encode(fh.read()).decode("ascii")
	except OSError:
		return _absolute_url(path)
	return f"data:{mime};base64,{b64}"


def _absolute_url(path: str) -> str:
	p = (path or "").strip()
	if not p:
		return ""
	if p.startswith("http://") or p.startswith("https://"):
		return p
	base = frappe.utils.get_url().rstrip("/")
	return urljoin(base + "/", p.lstrip("/"))

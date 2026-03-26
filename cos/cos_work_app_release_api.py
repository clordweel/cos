# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""合思协产（Cos Work App）版本分发：供客户端拉取最新发布元数据。"""

from __future__ import annotations

from urllib.parse import urljoin

import frappe
from frappe import _

ALLOWED_CHANNELS = frozenset({"stable", "beta", "internal"})


def _absolute_file_url(file_url: str) -> str:
	path = (file_url or "").strip()
	if not path:
		return ""
	if path.startswith("http://") or path.startswith("https://"):
		return path
	base = frappe.utils.get_url().rstrip("/")
	return urljoin(base + "/", path.lstrip("/"))


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_cos_work_app_release_latest(channel: str | None = "stable"):
	"""返回指定 channel 下 build_number 最大的启用版本。

	allow_guest=True：便于 App 在未登录会话时检查更新；仅返回已配置的公开字段，
	查询使用 ignore_permissions，不授予 Guest 对「Cos Work App Release」列表/表单的访问权限。

	若需收紧为仅登录用户或 API Key：将 allow_guest 改为 False，由会话或
	Authorization: token api_key:api_secret 调用本方法。
	"""
	ch = (channel or "stable").strip().lower()
	if ch not in ALLOWED_CHANNELS:
		frappe.throw(_("无效的分发渠道"), frappe.ValidationError)

	rows = frappe.get_all(
		"Cos Work App Release",
		filters={"channel": ch, "is_active": 1},
		fields=[
			"version",
			"build_number",
			"download_url",
			"apk_file",
			"release_notes",
			"sha256",
			"min_supported_build",
			"force_update",
		],
		order_by="build_number desc",
		limit_page_length=1,
		ignore_permissions=True,
	)

	if not rows:
		return {"ok": True, "channel": ch, "latest": None}

	row = rows[0]
	download = (row.get("download_url") or "").strip()
	if not download and row.get("apk_file"):
		download = _absolute_file_url(row["apk_file"])

	return {
		"ok": True,
		"channel": ch,
		"latest": {
			"version": row.get("version"),
			"build_number": row.get("build_number"),
			"download_url": download or None,
			"release_notes": row.get("release_notes") or "",
			"sha256": (row.get("sha256") or "").strip() or None,
			"min_supported_build": row.get("min_supported_build"),
			"force_update": bool(row.get("force_update")),
		},
	}

# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""合思协产（Cos Work App）版本分发：供客户端拉取最新发布元数据。"""

from __future__ import annotations

import frappe
from frappe import _

from cos.cos_share.utils.cos_work_app_release_public import (
	ALLOWED_CHANNELS,
	get_public_latest_release,
)


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
	return get_public_latest_release(ch)

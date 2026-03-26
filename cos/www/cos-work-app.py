# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""合思协产 App 公开分发页（Website），数据来自 Cos Work App Release。"""

import frappe

from cos.cos_share.utils.cos_work_app_release_public import (
	ALLOWED_CHANNELS,
	get_public_latest_release,
	list_channels_with_active_releases,
	resolve_channel,
)

no_cache = 1


def _channel_from_request():
	"""GET 查询参数在部分站点上下文中不会写入 form_dict，需同时读 request.args。"""
	q = None
	try:
		if getattr(frappe.local, "request", None) is not None:
			q = frappe.request.args.get("channel")
	except Exception:
		q = None
	if q:
		return q
	return frappe.form_dict.get("channel")


def get_context(context):
	ch = resolve_channel(_channel_from_request())
	data = get_public_latest_release(ch)
	context.update(data)
	context.allowed_channels = sorted(ALLOWED_CHANNELS)
	context.active_channels_hint = (
		list_channels_with_active_releases() if data.get("latest") is None else []
	)
	context.title = "合思协产 App 下载"
	context.no_sitemap = 1

# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""合思协产 App 公开分发页（Website），数据来自 Cos Work App Release。"""

import frappe

from cos.cos_share.utils.cos_work_app_release_public import (
	ALLOWED_CHANNELS,
	get_public_latest_release,
	resolve_channel,
)

no_cache = 1


def get_context(context):
	channel = frappe.form_dict.get("channel")
	ch = resolve_channel(channel)
	data = get_public_latest_release(ch)
	context.update(data)
	context.allowed_channels = sorted(ALLOWED_CHANNELS)
	context.title = "合思协产 App 下载"
	context.no_sitemap = 1

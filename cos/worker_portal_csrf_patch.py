# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""Worker Portal Bearer token 鉴权时跳过 CSRF 校验。

auth_hooks 在 validate_auth() 中执行，晚于 HTTPRequest.validate_csrf_token。
使用 Bearer wpt.xxx 的 POST 请求会因无 CSRF token 被拒绝。
本模块在应用加载时 patch validate_csrf_token，对有效 wpt token 放行。
"""

import frappe

WPT_PREFIX = "wpt."
CACHE_KEY_PREFIX = "worker_portal_token:"


def _is_valid_worker_portal_token() -> bool:
	"""检查当前请求是否携带有效的 Worker Portal Bearer token。"""
	if not getattr(frappe.local, "request", None):
		return False
	auth = frappe.get_request_header("Authorization") or ""
	parts = auth.split(" ", 1)
	if len(parts) != 2 or parts[0].lower() != "bearer":
		return False
	token = parts[1].strip()
	if not token.startswith(WPT_PREFIX):
		return False
	raw = token[len(WPT_PREFIX) :]
	return bool(frappe.cache.get_value(f"{CACHE_KEY_PREFIX}{raw}"))


def _patched_validate_csrf_token(self):
	if _is_valid_worker_portal_token():
		return
	return _original_validate_csrf_token(self)


def patch():
	"""Patch HTTPRequest.validate_csrf_token，对有效 wpt token 跳过 CSRF。"""
	global _original_validate_csrf_token
	import frappe.auth as auth_module  # 确保 auth 已加载（cos 加载时可能尚未加载）
	_original_validate_csrf_token = auth_module.HTTPRequest.validate_csrf_token
	auth_module.HTTPRequest.validate_csrf_token = _patched_validate_csrf_token

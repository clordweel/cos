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


def _is_login_for_token_request() -> bool:
	"""检查是否为 Worker Portal 登录接口（首次登录无 token，需豁免 CSRF）。

	validate_csrf_token 在 HTTPRequest 中执行，早于 frappe.api.handle，
	此时 form_dict.cmd 可能尚未从 URL 解析，故优先用 request.path 判断。
	"""
	req = getattr(frappe.local, "request", None)
	if not req:
		return False
	path = getattr(req, "path", "") or ""
	url = getattr(req, "url", "") or ""
	if "login_for_token" in path or "login_for_token" in url:
		return True
	cmd = getattr(frappe.local, "form_dict", None)
	if cmd and getattr(cmd, "cmd", None):
		return "login_for_token" in str(cmd.cmd)
	return False


def _patched_validate_csrf_token(self):
	if _is_valid_worker_portal_token():
		return
	if _is_login_for_token_request():
		return
	return _original_validate_csrf_token(self)


def patch():
	"""Patch HTTPRequest.validate_csrf_token，对有效 wpt token 跳过 CSRF。"""
	global _original_validate_csrf_token
	import importlib
	auth_module = importlib.import_module("frappe.auth")
	_original_validate_csrf_token = auth_module.HTTPRequest.validate_csrf_token
	auth_module.HTTPRequest.validate_csrf_token = _patched_validate_csrf_token

# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""Worker Portal Bearer token 鉴权时跳过 CSRF 校验。

auth_hooks 在 validate_auth() 中执行，晚于 HTTPRequest.validate_csrf_token。
使用 Bearer wpt.xxx 的 POST 请求会因无 CSRF token 被拒绝。
本模块在应用加载时 patch validate_csrf_token：对携带 ``Bearer wpt.`` 的请求跳过 CSRF
（不依赖缓存是否命中）；登录接口单独豁免。
"""

import frappe

WPT_PREFIX = "wpt."


def _looks_like_worker_portal_bearer() -> bool:
	"""请求是否携带 Portal 约定的 Bearer（前缀 wpt.）。

	说明：原先仅在 cache 命中时才跳过 CSRF；若 Redis 丢键、多 worker 缓存不一致、
	或 token 仍有效但缓存未命中，会导致 POST（如 approve_pi_logged_in）误报 CSRF，
	而 GET 正常。凡显式携带 ``Bearer wpt.`` 的 API 调用均视为 Portal 客户端发起：
	跨站表单无法伪造此头，后续仍由 auth_hooks 与 whitelist 校验 token/权限。
	"""
	if not getattr(frappe.local, "request", None):
		return False
	auth = frappe.get_request_header("Authorization") or ""
	parts = auth.split(" ", 1)
	if len(parts) != 2 or parts[0].lower() != "bearer":
		return False
	return parts[1].strip().startswith(WPT_PREFIX)


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
	if _looks_like_worker_portal_bearer():
		return
	if _is_login_for_token_request():
		return
	return _original_validate_csrf_token(self)


def patch():
	"""Patch HTTPRequest.validate_csrf_token：Portal Bearer wpt. 与 login_for_token 跳过 CSRF。"""
	global _original_validate_csrf_token
	import importlib
	auth_module = importlib.import_module("frappe.auth")
	_original_validate_csrf_token = auth_module.HTTPRequest.validate_csrf_token
	auth_module.HTTPRequest.validate_csrf_token = _patched_validate_csrf_token

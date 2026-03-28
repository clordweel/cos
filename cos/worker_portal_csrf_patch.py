# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""Worker Portal Bearer 与 COS 原生壳 API 的 CSRF 豁免。

auth_hooks 在 validate_auth() 中执行，晚于 HTTPRequest.validate_csrf_token。
使用 Bearer wpt.xxx 的 POST 请求会因无 CSRF token 被拒绝。
本模块在应用加载时 patch validate_csrf_token：对携带 ``Bearer wpt.`` 的请求跳过 CSRF
（不依赖缓存是否命中）；登录接口单独豁免；另对原生 App 以会话 Cookie 调用的少数
白名单方法（切换默认公司、小程序自选）跳过 CSRF。
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


# 原生壳（Flutter）仅用 sid + Cookie 头调用白名单 API，不经浏览器 Desk 下发 csrf_token；
# 与 Bearer wpt. 同理：跨站页面无法伪造本机 HttpClient 的 Cookie，仍由会话与 whitelist 鉴权。
_COS_NATIVE_COOKIE_API_MARKERS = (
	"company_context_api.set_default_company",
	"work_app_launcher_api.add_user_mini_program",
	"work_app_launcher_api.remove_user_mini_program",
)


def _is_cos_native_shell_cookie_api() -> bool:
	req = getattr(frappe.local, "request", None)
	if not req:
		return False
	path = (getattr(req, "path", "") or "").lower()
	url = (getattr(req, "url", "") or "").lower()
	combined = f"{path} {url}"
	return any(m in combined for m in _COS_NATIVE_COOKIE_API_MARKERS)


def _patched_validate_csrf_token(self):
	if _looks_like_worker_portal_bearer():
		return
	if _is_login_for_token_request():
		return
	if _is_cos_native_shell_cookie_api():
		return
	return _original_validate_csrf_token(self)


def patch():
	"""Patch HTTPRequest.validate_csrf_token：Portal / 原生壳约定路径跳过 CSRF。"""
	global _original_validate_csrf_token
	import importlib
	auth_module = importlib.import_module("frappe.auth")
	_original_validate_csrf_token = auth_module.HTTPRequest.validate_csrf_token
	auth_module.HTTPRequest.validate_csrf_token = _patched_validate_csrf_token

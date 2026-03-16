# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""Worker Portal API：供登录页/工作台检查登录状态，需 allow_guest 以支持 WebView/Capacitor 首次加载。"""

import frappe


@frappe.whitelist(allow_guest=True)
def get_logged_user():
	"""返回当前登录用户，Guest 时返回 'Guest'。供 worker-portal 登录页判断是否已登录。"""
	return frappe.session.user or "Guest"

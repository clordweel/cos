# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""Cos Work App WebView 壳顶栏占位：按请求路径匹配 COS Work Mini Program.launch_path，读取 nav_bar_inset_mode。

供 Website 模板与 Desk 内嵌壳统一使用（与 Flutter 弱化注入、H5+CSS 变量对齐）。
"""

from __future__ import annotations

import frappe


def is_cos_work_app_shell_user_agent(user_agent: str | None) -> bool:
	if not user_agent:
		return False
	return "CosWorkApp" in user_agent


def resolve_nav_bar_inset_mode_for_path(path: str | None) -> str | None:
	"""按最长匹配 launch_path 取 DocType 上的 nav_bar_inset_mode；无匹配返回 None。"""
	if not path:
		return None
	norm = path.rstrip("/") or "/"
	rows = frappe.get_all(
		"COS Work Mini Program",
		filters={"enabled": 1},
		fields=["launch_path", "nav_bar_inset_mode"],
		order_by="sort_order asc",
	)
	best_len = -1
	best_mode: str | None = None
	for r in rows:
		lp = (r.get("launch_path") or "").strip().rstrip("/")
		if not lp:
			continue
		if norm == lp or norm.startswith(lp + "/"):
			if len(lp) > best_len:
				best_len = len(lp)
				raw = (r.get("nav_bar_inset_mode") or "app_provided").strip()
				best_mode = raw if raw else "app_provided"
	return best_mode


def nav_bar_inset_mode_or_default(mode: str | None) -> str:
	m = (mode or "app_provided").strip()
	if m in ("none", "status_bar_only", "app_provided", "page_custom"):
		return m
	return "app_provided"


@frappe.whitelist()
def get_nav_bar_inset_for_path(path: str | None = None) -> dict:
	"""Desk / 壳内 H5 在运行时解析路径对应的顶栏占位（需登录）。"""
	p = (path or "").strip()
	if not p:
		try:
			p = getattr(frappe.request, "path", "") or ""
		except Exception:
			p = ""
	mode = resolve_nav_bar_inset_mode_for_path(p)
	return {"nav_bar_inset_mode": nav_bar_inset_mode_or_default(mode)}

# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""Cos Work App WebView 壳顶栏占位：按请求路径匹配 COS Work Mini Program.launch_path，读取 nav_bar_inset_mode。

供 Website 模板与 Desk 内嵌壳统一使用（与 Flutter 弱化注入、H5+CSS 变量对齐）。
H5 三档语义见 `public/css/cos_work_shell_inset.css` 文件头；Worker Portal 消费变量见 `COS_SHELL_CONTENT_PADDING_TOP_CSS`。
"""

from __future__ import annotations

import frappe

# 旧选项与历史取值（API 仍兼容解析）
_LEGACY_NAV_BAR_INSET = {
	"status_bar_only": "safe_area",
	"status_bar": "safe_area",
	"app_provided": "app_bar",
	"page_custom": "none",
}

_VALID_MODES = frozenset({"none", "safe_area", "app_bar"})


def is_cos_work_app_shell_user_agent(user_agent: str | None) -> bool:
	if not user_agent:
		return False
	return "CosWorkApp" in user_agent


def is_cos_work_app_shell_query(request_args) -> bool:
	"""首跳 URL 带 `__cos_work_shell=1` 时视为壳内打开（部分 WebView 首请求不带自定义 UA）。"""
	if not request_args:
		return False
	try:
		v = (request_args.get("__cos_work_shell") or "").strip().lower()
	except Exception:
		return False
	return v in ("1", "true", "yes")


def normalize_nav_bar_inset_mode(mode: str | None) -> str:
	"""统一为 none | safe_area | app_bar（默认 safe_area）。"""
	m = (mode or "").strip().lower()
	if not m:
		return "safe_area"
	m = _LEGACY_NAV_BAR_INSET.get(m, m)
	if m in _VALID_MODES:
		return m
	return "safe_area"


def resolve_nav_bar_inset_mode_for_path(path: str | None) -> str | None:
	"""按最长匹配 launch_path 取 DocType 上的 nav_bar_inset_mode；无匹配时 /app、/app/... 回退 desk_home。"""
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
				raw = (r.get("nav_bar_inset_mode") or "").strip()
				best_mode = raw if raw else "safe_area"
	if best_mode is not None:
		return best_mode
	# v16 工作台多为 /app、/app/...，与 fixture 中 desk_home 的 /desk 不一致；无更长 launch_path 匹配时回退 desk_home
	if norm == "/app" or norm.startswith("/app/"):
		desk_mode = frappe.db.get_value(
			"COS Work Mini Program",
			{"name": "desk_home", "enabled": 1},
			"nav_bar_inset_mode",
		)
		if desk_mode is not None:
			raw = (desk_mode or "").strip()
			return raw if raw else "safe_area"
	return None


def nav_bar_inset_mode_or_default(mode: str | None) -> str:
	return normalize_nav_bar_inset_mode(mode)


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

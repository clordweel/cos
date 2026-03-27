# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""合思协产 App 首页小程序宫格：由 DocType 配置 + 角色/用户绑定驱动。"""

import frappe
from frappe import _
from frappe.utils import cint


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.AuthenticationError)


def _merge_weights(role_rows, user_rows):
	"""program_docname -> 最小 sort_weight。"""
	best = {}
	for r in role_rows:
		n = r.get("mini_program")
		if not n:
			continue
		w = cint(r.get("sort_weight")) or 100
		if n not in best or w < best[n]:
			best[n] = w
	for r in user_rows:
		n = r.get("mini_program")
		if not n:
			continue
		w = cint(r.get("sort_weight")) or 50
		if n not in best or w < best[n]:
			best[n] = w
	return best


def _parse_accent(hex_str):
	s = (hex_str or "").strip()
	if not s:
		return ""
	if s.startswith("#") and len(s) == 7:
		return s
	if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
		return f"#{s}"
	return s


@frappe.whitelist()
def get_launcher_programs():
	"""返回当前用户可见、已启用的小程序列表（供移动端渲染宫格）。

	合并规则：用户「自选」与当前用户任一「角色默认」绑定的小程序取并集，
	同一小程序的多条绑定取最小 sort_weight 排序；再按目录 sort_order、标题排序。
	"""
	_require_login()
	user = frappe.session.user
	roles = frappe.get_roles(user)

	role_rows = frappe.get_all(
		"COS Work Mini Program Role",
		filters={"role": ["in", roles]},
		fields=["mini_program", "sort_weight"],
	)
	user_rows = frappe.get_all(
		"COS Work User Mini Program",
		filters={"user": user},
		fields=["mini_program", "sort_weight"],
	)

	weights = _merge_weights(role_rows, user_rows)
	if not weights:
		return []

	names = list(weights.keys())
	rows = frappe.get_all(
		"COS Work Mini Program",
		filters={"name": ["in", names], "enabled": 1},
		fields=[
			"name",
			"program_id",
			"title",
			"description",
			"launch_path",
			"auth_kind",
			"icon_key",
			"icon_url",
			"accent_color",
			"sort_order",
		],
	)

	def sort_key(r):
		doc_name = r.get("name")
		w = weights.get(doc_name, 999)
		so = cint(r.get("sort_order"))
		return (w, so, r.get("title") or "")

	rows.sort(key=sort_key)

	out = []
	for r in rows:
		out.append(
			{
				"id": r.get("program_id"),
				"title": r.get("title"),
				"subtitle": (r.get("description") or ""),
				"launch_path": r.get("launch_path"),
				"auth_kind": r.get("auth_kind") or "frappe_session",
				"icon_key": (r.get("icon_key") or "").strip(),
				"icon_url": (r.get("icon_url") or "").strip(),
				"accent_color": _parse_accent(r.get("accent_color")),
			}
		)
	return out

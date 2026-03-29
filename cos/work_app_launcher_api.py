# Copyright (c) 2025, bit and contributors
# License: MIT. See LICENSE

"""合思协产 App 首页小程序宫格：由 DocType 配置 + 角色/用户绑定驱动。"""

import frappe
from frappe import _
from frappe.utils import cint


def _require_login():
	# session.user 在部分边界请求下可能为 None（仅判断 != Guest 会漏掉，进而把 None 写入 Link 字段触发 User None not found）
	user = frappe.session.user
	if not user or user == "Guest":
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


def _row_to_launch_dict(r, *, user_pinned: bool = False) -> dict:
	"""单条 Doc 行 -> 与 get_launcher_programs 列表项一致的字典（供壳端 fromLauncherPayload）。"""
	nm = r.get("name")
	return {
		"doc_name": nm,
		"id": r.get("program_id"),
		"title": r.get("title"),
		"subtitle": (r.get("description") or ""),
		"launch_path": r.get("launch_path"),
		"auth_kind": r.get("auth_kind") or "frappe_session",
		"nav_bar_inset_mode": (r.get("nav_bar_inset_mode") or "status_bar_only").strip(),
		"show_nav_bar_title": cint(r.get("show_nav_bar_title", 1)),
		"icon_key": (r.get("icon_key") or "").strip(),
		"icon_url": (r.get("icon_url") or "").strip(),
		"accent_color": _parse_accent(r.get("accent_color")),
		"program_enabled": bool(cint(r.get("enabled"))),
		"user_pinned": user_pinned,
	}


@frappe.whitelist()
def get_mini_program_launch_config(program_id=None):
	"""按 program_id 拉取单条启动配置（不依赖是否出现在首页宫格）。

	供 Cos Work App 每次打开小程序前 GET；顶栏占位以 Website 模板+cos_work_shell_inset.css 及 Desk 侧 get_nav_bar_inset_for_path 为准；
	个人中心等入口使用内置 Registry 时也能合并服务端字段。
	"""
	_require_login()
	pid = (program_id or "").strip()
	if not pid:
		frappe.throw(_("Missing program_id"))

	user = frappe.session.user
	user_rows = frappe.get_all(
		"COS Work User Mini Program",
		filters={"user": user},
		fields=["mini_program"],
	)
	user_pinned_names = {r.get("mini_program") for r in user_rows if r.get("mini_program")}

	rows = frappe.get_all(
		"COS Work Mini Program",
		filters={"program_id": pid},
		fields=[
			"name",
			"program_id",
			"title",
			"description",
			"launch_path",
			"auth_kind",
			"nav_bar_inset_mode",
			"show_nav_bar_title",
			"icon_key",
			"icon_url",
			"accent_color",
			"sort_order",
			"enabled",
		],
		limit=1,
	)
	if not rows:
		return None
	r = rows[0]
	return _row_to_launch_dict(r, user_pinned=bool(r.get("name") in user_pinned_names))


@frappe.whitelist()
def get_launcher_programs():
	"""返回当前用户首页小程序列表（供移动端渲染宫格）。

	合并规则：用户「自选」与当前用户任一「角色默认」绑定的小程序取并集，
	同一小程序的多条绑定取最小 sort_weight 排序；再按目录 sort_order、标题排序。

	管理员取消「启用」后仍返回该条目，并带 program_enabled=false，
	便于客户端灰显占位；用户自选记录不会在后台被自动删除。
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
	user_pinned_names = {r.get("mini_program") for r in user_rows if r.get("mini_program")}

	weights = _merge_weights(role_rows, user_rows)
	if not weights:
		return []

	names = list(weights.keys())
	rows = frappe.get_all(
		"COS Work Mini Program",
		filters={"name": ["in", names]},
		fields=[
			"name",
			"program_id",
			"title",
			"description",
			"launch_path",
			"auth_kind",
			"nav_bar_inset_mode",
			"show_nav_bar_title",
			"icon_key",
			"icon_url",
			"accent_color",
			"sort_order",
			"enabled",
		],
	)

	def sort_key(r):
		doc_name = r.get("name")
		w = weights.get(doc_name, 999)
		so = cint(r.get("sort_order"))
		en = cint(r.get("enabled"))
		# 已启用的排在前，停用仍保留在首页时排在后
		return (0 if en else 1, w, so, r.get("title") or "")

	rows.sort(key=sort_key)

	out = []
	for r in rows:
		nm = r.get("name")
		out.append(_row_to_launch_dict(r, user_pinned=bool(nm in user_pinned_names)))
	return out


@frappe.whitelist()
def get_market_programs():
	"""返回「在市场展示」且已启用的小程序，并标注当前用户是否在首页可见、是否自选添加。

	首页可见 = 与 get_launcher_programs 相同（角色默认 ∪ 用户自选）。
	自选 = 存在「用户自选小程序」记录。
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
	user_pinned_names = {r.get("mini_program") for r in user_rows if r.get("mini_program")}
	weights = _merge_weights(role_rows, user_rows)

	market_rows = frappe.get_all(
		"COS Work Mini Program",
		filters={"enabled": 1, "show_in_market": 1},
		fields=[
			"name",
			"program_id",
			"title",
			"description",
			"launch_path",
			"auth_kind",
			"nav_bar_inset_mode",
			"show_nav_bar_title",
			"icon_key",
			"icon_url",
			"accent_color",
			"sort_order",
		],
		order_by="sort_order asc, title asc",
	)

	out = []
	for r in market_rows:
		nm = r.get("name")
		out.append(
			{
				"doc_name": nm,
				"id": r.get("program_id"),
				"title": r.get("title"),
				"subtitle": (r.get("description") or ""),
				"launch_path": r.get("launch_path"),
				"auth_kind": r.get("auth_kind") or "frappe_session",
				"nav_bar_inset_mode": (r.get("nav_bar_inset_mode") or "status_bar_only").strip(),
				"show_nav_bar_title": cint(r.get("show_nav_bar_title", 1)),
				"icon_key": (r.get("icon_key") or "").strip(),
				"icon_url": (r.get("icon_url") or "").strip(),
				"accent_color": _parse_accent(r.get("accent_color")),
				"in_launcher": bool(nm in weights),
				"user_pinned": bool(nm in user_pinned_names),
			}
		)
	return out


@frappe.whitelist()
def add_user_mini_program(mini_program):
	"""将小程序加入当前用户的「自选」，首页宫格会出现（若已因角色可见则仅补自选记录）。"""
	_require_login()
	mini_program = (mini_program or "").strip()
	if not mini_program:
		frappe.throw(_("未指定小程序"))
	if not frappe.db.exists("COS Work Mini Program", mini_program):
		frappe.throw(_("小程序不存在"))
	doc = frappe.get_cached_doc("COS Work Mini Program", mini_program)
	if not doc.enabled:
		frappe.throw(_("小程序已停用"))
	if not doc.show_in_market:
		frappe.throw(_("该小程序未对市场开放"))
	user = frappe.session.user
	if frappe.db.exists(
		"COS Work User Mini Program",
		{"user": user, "mini_program": mini_program},
	):
		return {"ok": True, "already": True}
	row = frappe.get_doc(
		{
			"doctype": "COS Work User Mini Program",
			"user": user,
			"mini_program": mini_program,
			"sort_weight": 50,
		}
	)
	row.insert()
	return {"ok": True, "already": False}


@frappe.whitelist()
def remove_user_mini_program(mini_program):
	"""移除当前用户自选；若仍绑定角色，首页仍可能显示该小程序。"""
	_require_login()
	mini_program = (mini_program or "").strip()
	if not mini_program:
		frappe.throw(_("未指定小程序"))
	user = frappe.session.user
	name = frappe.db.get_value(
		"COS Work User Mini Program",
		{"user": user, "mini_program": mini_program},
		"name",
	)
	if not name:
		frappe.throw(_("没有可移除的自选记录"))
	frappe.delete_doc("COS Work User Mini Program", name)
	return {"ok": True}

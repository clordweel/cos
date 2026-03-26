# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""Cos Work App 发布信息：网站/API 共用的只读查询（ignore_permissions，仅返回公开字段）。"""

from __future__ import annotations

from urllib.parse import urljoin

import frappe

ALLOWED_CHANNELS = frozenset({"stable", "beta", "internal"})


def _truthy_is_active(value) -> bool:
	"""兼容 Check 在库中 0/1、布尔、字符串等差异（避免 ORM filters 与库值不一致导致查不到）。"""
	if value is None:
		return False
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return int(value) != 0
	s = str(value).strip().lower()
	return s in ("1", "yes", "true", "on", "是", "y", "t")


def _absolute_file_url(file_url: str) -> str:
	path = (file_url or "").strip()
	if not path:
		return ""
	if path.startswith("http://") or path.startswith("https://"):
		return path
	base = frappe.utils.get_url().rstrip("/")
	return urljoin(base + "/", path.lstrip("/"))


def resolve_channel(channel: str | None, *, fallback: str = "stable") -> str:
	ch = (channel or fallback).strip().lower()
	if ch not in ALLOWED_CHANNELS:
		return fallback
	return ch


def list_channels_with_active_releases() -> list[str]:
	"""存在「启用」发布记录的分发渠道（供网站空态提示）。"""
	rows = frappe.get_all(
		"Cos Work App Release",
		fields=["channel", "is_active"],
		limit_page_length=500,
		ignore_permissions=True,
	)
	found = set()
	for r in rows or []:
		if not _truthy_is_active(r.get("is_active")):
			continue
		key = (r.get("channel") or "").strip().lower()
		if key in ALLOWED_CHANNELS:
			found.add(key)
	return sorted(found)


def get_public_latest_release(channel: str | None = "stable") -> dict:
	"""返回 { ok, channel, latest }；latest 为 None 表示当前渠道无启用发布。"""
	ch = resolve_channel(channel)
	# 不在 ORM 里过滤 is_active：部分环境下 Check 与整数 1 比较会漏行；改在 Python 判断。
	candidates = frappe.get_all(
		"Cos Work App Release",
		filters={"channel": ch},
		fields=[
			"version",
			"build_number",
			"download_url",
			"apk_file",
			"release_notes",
			"sha256",
			"min_supported_build",
			"force_update",
			"is_active",
		],
		order_by="build_number desc",
		limit_page_length=50,
		ignore_permissions=True,
	)
	active_rows = [r for r in (candidates or []) if _truthy_is_active(r.get("is_active"))]
	if not active_rows:
		# 回退：渠道字段若含首尾空格等，与 ORM 精确匹配可能失败
		wide = frappe.get_all(
			"Cos Work App Release",
			fields=[
				"channel",
				"version",
				"build_number",
				"download_url",
				"apk_file",
				"release_notes",
				"sha256",
				"min_supported_build",
				"force_update",
				"is_active",
			],
			order_by="build_number desc",
			limit_page_length=200,
			ignore_permissions=True,
		)
		active_rows = [
			r
			for r in (wide or [])
			if _truthy_is_active(r.get("is_active"))
			and (r.get("channel") or "").strip().lower() == ch
		]
	if not active_rows:
		return {"ok": True, "channel": ch, "latest": None}

	row = max(active_rows, key=lambda x: int(x.get("build_number") or 0))
	download = (row.get("download_url") or "").strip()
	if not download and row.get("apk_file"):
		download = _absolute_file_url(row["apk_file"])

	return {
		"ok": True,
		"channel": ch,
		"latest": {
			"version": row.get("version"),
			"build_number": row.get("build_number"),
			"download_url": download or None,
			"release_notes": row.get("release_notes") or "",
			"sha256": (row.get("sha256") or "").strip() or None,
			"min_supported_build": row.get("min_supported_build"),
			"force_update": bool(row.get("force_update")),
		},
	}

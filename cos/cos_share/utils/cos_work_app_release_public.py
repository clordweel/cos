# Copyright (c) 2026, BIoT and contributors
# For license information, please see license.txt

"""Cos Work App 发布信息：网站/API 共用的只读查询（ignore_permissions，仅返回公开字段）。"""

from __future__ import annotations

from urllib.parse import urljoin

import frappe

ALLOWED_CHANNELS = frozenset({"stable", "beta", "internal"})


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


def get_public_latest_release(channel: str | None = "stable") -> dict:
	"""返回 { ok, channel, latest }；latest 为 None 表示当前渠道无启用发布。"""
	ch = resolve_channel(channel)
	rows = frappe.get_all(
		"Cos Work App Release",
		filters={"channel": ch, "is_active": 1},
		fields=[
			"version",
			"build_number",
			"download_url",
			"apk_file",
			"release_notes",
			"sha256",
			"min_supported_build",
			"force_update",
		],
		order_by="build_number desc",
		limit_page_length=1,
		ignore_permissions=True,
	)

	if not rows:
		return {"ok": True, "channel": ch, "latest": None}

	row = rows[0]
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

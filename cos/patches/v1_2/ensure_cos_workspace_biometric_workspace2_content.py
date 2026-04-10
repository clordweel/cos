"""已跑过旧版 ensure_cos_workspace_biometric_links 的站点补写 Workspace 2.0 content 卡片。

Desk Workspace 2.0 仅渲染 content 中声明的 card；仅 links 子表不足以显示「考勤同步」。
"""
from __future__ import annotations

import frappe

from cos.patches.v1_2.ensure_cos_workspace_biometric_links import (
	CARD_LABEL,
	WORKSPACE_NAME,
	_ensure_content,
)


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	if not _ensure_content(ws):
		return

	ws.flags.ignore_links = True
	ws.save(ignore_permissions=True)

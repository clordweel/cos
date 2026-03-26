"""确保 COS 工作台显示「合思协产 App」卡片及 Cos Work App Release 链接。

Desk Workspace 2.0 仅渲染 content 中声明的 card；仅改 links 子表不足以显示新卡片。
站点上已存在的 Workspace 记录不会随模块内 JSON 自动合并时，由本 patch 幂等补齐。
"""
from __future__ import annotations

import json
import uuid

import frappe


WORKSPACE_NAME = "COS"
CARD_NAME = "合思协产 App"
LINK_LABEL = "版本与分发"
LINK_TO = "Cos Work App Release"


def _content_has_card(content: str | None, card_name: str) -> bool:
	try:
		blocks = json.loads(content or "[]")
	except json.JSONDecodeError:
		return False
	if not isinstance(blocks, list):
		return False
	for b in blocks:
		if not isinstance(b, dict):
			continue
		if b.get("type") != "card":
			continue
		data = b.get("data") or {}
		if data.get("card_name") == card_name:
			return True
	return False


def _ensure_content(ws) -> bool:
	if _content_has_card(ws.content, CARD_NAME):
		return False
	try:
		blocks = json.loads(ws.content or "[]")
	except json.JSONDecodeError:
		blocks = []
	if not isinstance(blocks, list):
		blocks = []
	blocks.append(
		{
			"id": uuid.uuid4().hex[:10],
			"type": "card",
			"data": {"card_name": CARD_NAME, "col": 4},
		}
	)
	ws.content = json.dumps(blocks, ensure_ascii=False)
	return True


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	dirty = False

	has_break = False
	has_link = False
	for row in ws.links:
		if row.type == "Card Break" and (row.label or "") == CARD_NAME:
			has_break = True
		if row.type == "Link" and (row.link_to or "") == LINK_TO:
			has_link = True

	if not has_break:
		ws.append(
			"links",
			{
				"type": "Card Break",
				"label": CARD_NAME,
				"link_type": "DocType",
				"hidden": 0,
				"link_count": 1,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
		dirty = True

	if not has_link:
		ws.append(
			"links",
			{
				"type": "Link",
				"label": LINK_LABEL,
				"link_to": LINK_TO,
				"link_type": "DocType",
				"hidden": 0,
				"link_count": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
		dirty = True

	if _ensure_content(ws):
		dirty = True

	if dirty:
		ws.flags.ignore_links = True
		ws.save(ignore_permissions=True)

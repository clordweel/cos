"""在 COS 工作台「合思协产 App」卡片下增加工作台小程序相关 DocType 链接，并修正 link_count。"""
from __future__ import annotations

import frappe

WORKSPACE_NAME = "COS"
CARD_LABEL = "合思协产 App"

NEW_LINKS = [
	("工作台小程序", "COS Work Mini Program"),
	("角色默认小程序", "COS Work Mini Program Role"),
	("用户自选小程序", "COS Work User Mini Program"),
]


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	dirty = False

	existing = {(row.link_to or "") for row in ws.links if row.type == "Link"}

	for label, link_to in NEW_LINKS:
		if link_to in existing:
			continue
		ws.append(
			"links",
			{
				"type": "Link",
				"label": label,
				"link_to": link_to,
				"link_type": "DocType",
				"hidden": 0,
				"link_count": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
		existing.add(link_to)
		dirty = True

	for i, row in enumerate(ws.links):
		if row.type == "Card Break" and (row.label or "") == CARD_LABEL:
			cnt = 0
			for j in range(i + 1, len(ws.links)):
				r = ws.links[j]
				if r.type == "Card Break":
					break
				if r.type == "Link":
					cnt += 1
			if row.link_count != cnt:
				row.link_count = cnt
				dirty = True
			break

	if dirty:
		ws.flags.ignore_links = True
		ws.save(ignore_permissions=True)

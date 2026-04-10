"""在 COS 工作台增加「考勤同步」卡片与相关 DocType 链接。"""
from __future__ import annotations

import frappe

WORKSPACE_NAME = "COS"
CARD_LABEL = "考勤同步"

NEW_LINKS = [
	("考勤机", "Biometric Device"),
	("考勤同步设置", "Biometric Sync Settings"),
	("考勤机操作日志", "Biometric Device Action Log"),
]


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	dirty = False

	existing = {(row.link_to or "") for row in ws.links if row.type == "Link"}
	missing = [(lab, lt) for lab, lt in NEW_LINKS if lt not in existing]
	if not missing:
		return

	card_labels = {(row.label or "") for row in ws.links if row.type == "Card Break"}
	if CARD_LABEL not in card_labels:
		ws.append(
			"links",
			{
				"type": "Card Break",
				"label": CARD_LABEL,
				"link_count": len(NEW_LINKS),
				"link_type": "DocType",
				"hidden": 0,
				"is_query_report": 0,
				"onboard": 0,
			},
		)
		dirty = True

	for label, link_to in missing:
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

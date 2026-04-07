# Copyright (c) 2026, COS and contributors
# License: MIT. See license.txt

"""采购入库单 title 占位符临时修补。

ERPNext 在 Purchase Receipt 上曾为隐藏字段 title 设置 default「{supplier_name}」；部分建单路径（如从 PO 生成）
下 Frappe set_title_field 未把模板解析为 supplier_name，导致界面/库中仍为字面量。

上游修复：frappe/erpnext#54051（移除 title 字段，title_field 改为 supplier_name）。该补丁在「仍存在 title 字段」
时生效；升级 ERPNext 并 migrate 后 title 字段若已删除，本函数立即 no-op，可整文件删除。

参见：document.Document.set_title_field（仅当 title 为空时才对 default 做 format）。
"""


def fix_title_if_unresolved_placeholder(doc, method=None):
	if not doc.meta.get_field("title"):
		return
	if (doc.get("title") or "").strip() != "{supplier_name}":
		return
	sn = (doc.get("supplier_name") or "").strip()
	if not sn:
		return
	doc.set("title", sn)

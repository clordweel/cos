# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
电商采购：Purchase Order 保存前，根据 Item 的 custom_purchase_sources 自动填充
采购平台、平台 SKU、采购链接。支持主采购链接（is_primary）优先带出。
"""

import frappe


def on_purchase_order_before_save(doc, method=None):
    """PO 保存前：从 Item 采购来源子表带出采购平台、SKU、链接。
    - 若已选 custom_platform：按平台匹配带出 SKU、链接。
    - 若未选 custom_platform：使用主采购链接（is_primary=1），若无则取第一条，带出平台、SKU、链接。
    """
    for item in doc.items or []:
        if not item.item_code:
            continue
        _fill_from_item_sources(item)


def _fill_from_item_sources(item):
    """从 Item 的 custom_purchase_sources 填充 PO 明细行的采购平台、SKU、链接。"""
    # 若三个字段均已填充，跳过
    if (
        item.get("custom_platform")
        and item.get("custom_platform_sku")
        and item.get("custom_purchase_url")
    ):
        return

    if item.get("custom_platform"):
        # 已选平台：按平台匹配，仅补充 SKU、链接
        sources = frappe.get_all(
            "Item Purchase Source",
            filters={
                "parent": item.item_code,
                "parenttype": "Item",
                "platform": item.custom_platform,
            },
            fields=["platform_sku", "purchase_url"],
            limit=1,
        )
    else:
        # 未选平台：优先主采购，否则取第一条
        sources = _get_primary_or_first_source(item.item_code)

    if not sources:
        return

    s = sources[0]
    if not item.get("custom_platform"):
        item.custom_platform = s.get("platform") or ""
    if not item.get("custom_platform_sku"):
        item.custom_platform_sku = s.get("platform_sku") or ""
    if not item.get("custom_purchase_url"):
        item.custom_purchase_url = s.get("purchase_url") or ""


def _get_primary_or_first_source(item_code):
    """获取主采购来源，若无则取第一条。"""
    # 检查 is_primary 列是否存在（兼容未迁移环境）
    if not frappe.db.has_column("Item Purchase Source", "is_primary"):
        return frappe.get_all(
            "Item Purchase Source",
            filters={"parent": item_code, "parenttype": "Item"},
            fields=["platform", "platform_sku", "purchase_url"],
            order_by="idx asc",
            limit=1,
        )
    # 优先主采购
    primary = frappe.get_all(
        "Item Purchase Source",
        filters={
            "parent": item_code,
            "parenttype": "Item",
            "is_primary": 1,
        },
        fields=["platform", "platform_sku", "purchase_url"],
        limit=1,
    )
    if primary:
        return primary
    # 无主采购时取第一条
    return frappe.get_all(
        "Item Purchase Source",
        filters={"parent": item_code, "parenttype": "Item"},
        fields=["platform", "platform_sku", "purchase_url"],
        order_by="idx asc",
        limit=1,
    )


@frappe.whitelist()
def get_primary_purchase_source(item_code):
    """获取物料的主采购来源（供前端即时带出）。"""
    if not item_code:
        return None
    sources = _get_primary_or_first_source(item_code)
    return sources[0] if sources else None

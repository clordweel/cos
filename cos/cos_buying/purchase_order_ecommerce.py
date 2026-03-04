# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
电商采购：Purchase Order 保存前，根据 Item 的 custom_purchase_sources 自动填充
custom_platform_sku、custom_purchase_url。
"""

import frappe


def on_purchase_order_before_save(doc, method=None):
    """PO 保存前：若 items 行有 item_code 和 custom_platform，从 Item 采购来源子表带出 SKU 和链接。"""
    for item in doc.items or []:
        if not item.item_code or not item.get("custom_platform"):
            continue
        if item.get("custom_platform_sku") and item.get("custom_purchase_url"):
            continue
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
        if sources:
            s = sources[0]
            if not item.get("custom_platform_sku"):
                item.custom_platform_sku = s.get("platform_sku") or ""
            if not item.get("custom_purchase_url"):
                item.custom_purchase_url = s.get("purchase_url") or ""

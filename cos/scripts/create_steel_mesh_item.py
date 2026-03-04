"""创建钢网网片物料（规格宽1米长2米，用途内部项目焊接仓库围挡）。

用法:
  bench --site junhai.local execute cos.scripts.create_steel_mesh_item.run
"""
from __future__ import annotations


def run(site: str | None = None) -> str:
    """创建钢网网片 Item。"""
    import frappe

    frappe.connect(site=site)

    item_code = "GW-WP-1000-2000"  # 钢网-网片-宽1000-长2000
    if frappe.db.exists("Item", item_code):
        return f"ALREADY_EXISTS:{item_code}"

    doc = frappe.new_doc("Item")
    doc.naming_series = "{custom_unique_item_name}"
    doc.custom_unique_item_name = item_code
    doc.item_name = "钢网网片 1m×2m"
    doc.description = "内部项目焊接仓库围挡"
    doc.item_group = "型材"
    doc.stock_uom = "张"
    doc.is_stock_item = 1
    doc.insert()
    frappe.db.commit()
    return f"CREATED:{item_code}"

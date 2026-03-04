"""在 dev 服务器上通过 bench execute 将电商采购平台从 Select 改为 Link(Source Type)。

用法:
  bench --site junhai.local execute cos.scripts.migrate_ecommerce_to_source_type.run
"""
from __future__ import annotations

import json


PLATFORMS = ["京东", "1688", "淘宝/天猫", "拼多多", "工品汇", "其他"]


def run(site: str | None = None) -> str:
    """执行迁移：预设 Source Type、修改 platform 字段为 Link(Source Type)。"""
    import frappe

    frappe.connect(site=site)
    created = {}

    # 1) 创建 Source Type 预设（京东、1688 等）
    meta = frappe.get_meta("Source Type")
    name_field = "source_name" if meta.has_field("source_name") else ("source_type_name" if meta.has_field("source_type_name") else "name")

    for name in PLATFORMS:
        if frappe.db.exists("Source Type", name):
            # 更新已有记录：related_doctype、module
            doc = frappe.get_doc("Source Type", name)
            if doc.related_doctype != "Item Purchase Source" or doc.module != "COS Buying":
                doc.related_doctype = "Item Purchase Source"
                doc.module = "COS Buying"
                doc.save()
                created[f"st_{name}"] = "updated"
            else:
                created[f"st_{name}"] = "already_exists"
        else:
            doc = frappe.new_doc("Source Type")
            setattr(doc, name_field, name)
            doc.related_doctype = "Item Purchase Source"
            doc.module = "COS Buying"
            doc.insert()
            created[f"st_{name}"] = "created"

    # 2) 确保 Item Purchase Source 的 module 为 COS Buying，platform 为 Link(Source Type)
    ips_dt = frappe.get_doc("DocType", "Item Purchase Source")
    if ips_dt.module != "COS Buying":
        ips_dt.module = "COS Buying"
        ips_dt.save()
        created["ips_module"] = "updated"
    platform_field = next((f for f in ips_dt.fields if f.fieldname == "platform"), None)
    if platform_field:
        if platform_field.fieldtype == "Link" and platform_field.options == "Source Type":
            created["ips_platform"] = "already_link"
        else:
            platform_field.fieldtype = "Link"
            platform_field.options = "Source Type"
            platform_field.link_filters = '[[\"Source Type\",\"related_doctype\",\"=\",\"Item Purchase Source\"]]'
            platform_field.save()
            created["ips_platform"] = "updated"
    else:
        created["ips_platform"] = "field_not_found"

    # 3) 修改 Purchase Order Item custom_platform：Select -> Link(Source Type)
    # 注：Custom Field 的 save() 会校验 fieldtype 不可变更，故用 db.set_value 直接更新
    cf = frappe.db.get_value(
        "Custom Field",
        {"dt": "Purchase Order Item", "fieldname": "custom_platform"},
        ["name", "fieldtype", "options"],
        as_dict=True,
    )
    if cf:
        if cf.fieldtype == "Link" and cf.options == "Source Type":
            # 确保 link_filters 正确
            link_filters = '[[\"Source Type\",\"related_doctype\",\"=\",\"Item Purchase Source\"]]'
            if frappe.db.get_value("Custom Field", cf.name, "link_filters") != link_filters:
                frappe.db.set_value("Custom Field", cf.name, "link_filters", link_filters)
                created["po_platform"] = "link_filters_updated"
            else:
                created["po_platform"] = "already_link"
        else:
            frappe.db.set_value("Custom Field", cf.name, "fieldtype", "Link")
            frappe.db.set_value("Custom Field", cf.name, "options", "Source Type")
            frappe.db.set_value("Custom Field", cf.name, "link_filters", '[[\"Source Type\",\"related_doctype\",\"=\",\"Item Purchase Source\"]]')
            created["po_platform"] = "updated"
    else:
        created["po_platform"] = "cf_not_found"

    frappe.db.commit()
    return json.dumps(created, ensure_ascii=False, indent=2)

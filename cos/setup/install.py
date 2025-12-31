# import frappe

# def after_install():
#     """App 安装后执行一次"""
#     sync_custom_settings()

# def after_migrate():
#     """每次 bench migrate 后执行"""
#     sync_custom_settings()

# def sync_custom_settings():
#     """
#     在这里通过代码更新标准 DocType 的属性。
#     这比 Property Setter Fixture 更安全，因为它在所有字段同步完成后执行。
#     """
#     # 修复你之前的错误：在字段确保存在后，再设置 search_fields
#     if frappe.db.exists("DocType", "Item Group"):
#         frappe.db.set_value("DocType", "Item Group", "search_fields", 
#             "parent_item_group,custom_code,custom_description")
    
#     # 强制清理缓存使设置生效
#     frappe.clear_cache(doctype="Item Group")
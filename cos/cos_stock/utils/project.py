import frappe


def auto_set_project_code(doc, method=None):
    """
    Hooks: Project > before_insert
    功能：支持手动编码：当选择 {custom_customer_provided_project_number} 时，直接使用该字段值作为项目编号
    """

    # 如果用户选择了手动编码模式
    if doc.naming_series == "{custom_customer_provided_project_number}":
        # 验证 custom_customer_provided_project_number 是否有值
        if not doc.custom_customer_provided_project_number:
            frappe.throw(
                title="手动编码失败",
                msg="选择了手动编码模式，但未填写客户提供项目编号 (Customer Provided Project Number)。",
            )
        
        # 直接使用 custom_customer_provided_project_number 的值作为项目编号
        # 设置 name 和标志，跳过 Frappe 的命名系列机制
        doc.name = doc.custom_customer_provided_project_number
        doc.flags.name_set = True  # 告诉 Frappe 名称已设置，跳过自动命名
        return

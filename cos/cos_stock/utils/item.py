import frappe


def auto_set_item_code(doc, method=None):
    """
    Hooks: Item > before_insert
    功能：根据物料组的 custom_code 自动设置 naming_series。
    支持手动编码：当选择 {custom_unique_item_name} 时，直接使用该字段值作为物料编号。
    注：基础名缩写不参与此处流水号生成，仅用于约束 Agent 从物料参数模板生成物料时的编码规范。
    """

    # 1. 如果用户选择了手动编码模式
    if doc.naming_series == "{custom_unique_item_name}":
        if not doc.custom_unique_item_name:
            frappe.throw(
                title="手动编码失败",
                msg="选择了手动编码模式，但未填写唯一物料编码 (Unique Item Name)。",
            )
        doc.name = doc.custom_unique_item_name
        doc.flags.name_set = True
        return

    # 2. 检查是否选择了物料组
    if not doc.item_group:
        return

    # 3. 获取物料组的 custom_code
    group_code = frappe.db.get_value("Item Group", doc.item_group, "custom_code")
    if group_code:
        doc.naming_series = f"{group_code}.####"
    else:
        frappe.throw(
            title="编号生成失败",
            msg=f"物料组 <b>{doc.item_group}</b> 未配置编码前缀 (Custom Code)。<br>请先在物料组中设置代码（如 1010），或选择正确的末级分组。",
        )

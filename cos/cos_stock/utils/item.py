import frappe


def auto_set_item_code(doc, method=None):
    """
    Hooks: Item > before_validate 或 before_insert
    功能：根据物料组的 custom_code 自动设置 naming_series
    支持手动编码：当选择 {custom_unique_item_name} 时，直接使用该字段值作为物料编号
    """

    # 1. 如果用户选择了手动编码模式
    if doc.naming_series == "{custom_unique_item_name}":
        # 验证 custom_unique_item_name 是否有值
        if not doc.custom_unique_item_name:
            frappe.throw(
                title="手动编码失败",
                msg="选择了手动编码模式，但未填写唯一物料编码 (Unique Item Name)。",
            )
        
        # 直接使用 custom_unique_item_name 的值作为 item_code
        # 设置 name 和标志，跳过 Frappe 的命名系列机制
        doc.name = doc.custom_unique_item_name
        doc.flags.name_set = True  # 告诉 Frappe 名称已设置，跳过自动命名
        return

    # 2. 检查是否选择了物料组
    if not doc.item_group:
        return

    # 3. 获取物料组的 custom_code (直接取值，无需加载整个 Item Group 对象，效率更高)
    group_code = frappe.db.get_value("Item Group", doc.item_group, "custom_code")


    # 4. 核心逻辑：自动编码模式
    if group_code:
        # 直接构造目标格式：代码 + .####
        # 结果示例：1010.####
        target_series = f"{group_code}.####"

        # 赋值给单据
        doc.naming_series = target_series

    else:
        # 5. 防呆机制：如果物料组没有配置代码，抛出错误阻止保存
        # 这样可以防止生成错误的编号，强制要求维护好基础数据
        frappe.throw(
            title="编号生成失败",
            msg=f"物料组 <b>{doc.item_group}</b> 未配置编码前缀 (Custom Code)。<br>请先在物料组中设置代码（如 1010），或选择正确的末级分组。",
        )

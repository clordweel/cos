"""
公司税费模板控制器
处理公司进销项税费模板的初始化和管理
"""
import frappe
from frappe import _


def _delete_default_china_tax_templates(company):
    """
    删除系统默认创建的 China Tax 税费模板
    
    识别规则：
    1. 标题包含 "China" 或 "中国" 关键字
    2. 但不是我们自定义的格式（"中国增值税 - X% (销项/进项)"）
    3. 或者是 ERPNext 系统默认创建的模板格式
    
    Args:
        company: 公司名称
    
    Returns:
        dict: 删除结果统计
    """
    deleted_count = 0
    deleted_templates = []
    
    # 查找所有销售税费模板（排除我们自定义的格式）
    sales_templates = frappe.db.get_all(
        "Sales Taxes and Charges Template",
        filters={
            "company": company,
            "title": ["not like", "中国增值税%"]
        },
        fields=["name", "title"]
    )
    
    # 检查是否是系统默认创建的 China 相关模板
    for template in sales_templates:
        title = template.get("title", "").strip()
        title_lower = title.lower()
        
        # 识别系统默认模板：包含 china/chinese/中国 关键字，但不是我们的自定义格式
        is_system_default = (
            ("china" in title_lower or "chinese" in title_lower or "中国" in title) 
            and "中国增值税" not in title
        ) or (
            # 也可能是类似 "Standard China" 或 "China Tax" 这样的格式
            title_lower in ["china tax", "china taxes", "中国税", "中国税费"]
        )
        
        if is_system_default:
            try:
                frappe.delete_doc(
                    "Sales Taxes and Charges Template",
                    template["name"],
                    force=1,
                    ignore_permissions=True
                )
                deleted_count += 1
                deleted_templates.append(f"销售: {title}")
                frappe.logger().info(f"删除系统默认销售税费模板: {title}")
            except Exception as e:
                frappe.logger().error(f"删除销售税费模板失败 {template['name']}: {str(e)}")
    
    # 查找所有采购税费模板（排除我们自定义的格式）
    purchase_templates = frappe.db.get_all(
        "Purchase Taxes and Charges Template",
        filters={
            "company": company,
            "title": ["not like", "中国增值税%"]
        },
        fields=["name", "title"]
    )
    
    for template in purchase_templates:
        title = template.get("title", "").strip()
        title_lower = title.lower()
        
        is_system_default = (
            ("china" in title_lower or "chinese" in title_lower or "中国" in title) 
            and "中国增值税" not in title
        ) or (
            title_lower in ["china tax", "china taxes", "中国税", "中国税费"]
        )
        
        if is_system_default:
            try:
                frappe.delete_doc(
                    "Purchase Taxes and Charges Template",
                    template["name"],
                    force=1,
                    ignore_permissions=True
                )
                deleted_count += 1
                deleted_templates.append(f"采购: {title}")
                frappe.logger().info(f"删除系统默认采购税费模板: {title}")
            except Exception as e:
                frappe.logger().error(f"删除采购税费模板失败 {template['name']}: {str(e)}")
    
    if deleted_count > 0:
        frappe.db.commit()
    
    return {
        "count": deleted_count,
        "templates": deleted_templates
    }


def _make_idempotent_template(
    company, doctype, title, account_number, backup_name, rate, is_default
):
    """
    创建或更新税费模板（幂等操作）
    如果模板已存在，则跳过创建
    
    Args:
        company: 公司名称
        doctype: 模板类型（Sales Taxes and Charges Template 或 Purchase Taxes and Charges Template）
        title: 模板标题
        account_number: 科目编号
        backup_name: 备用科目名称
        rate: 税率
        is_default: 是否默认
    
    Returns:
        tuple: (是否创建/更新, 模板名称或 None)
    """
    child_doctype = (
        "Sales Taxes and Charges"
        if doctype == "Sales Taxes and Charges Template"
        else "Purchase Taxes and Charges"
    )

    # 1. 检查模板是否已存在
    existing_name = frappe.db.get_value(
        doctype, {"title": title, "company": company}
    )
    
    # 如果已存在，跳过创建
    if existing_name:
        frappe.logger().info(
            f"模板已存在，跳过创建: {title} (公司: {company})"
        )
        return (False, existing_name)

    # 2. 多维度查找科目
    account_head = frappe.db.get_value(
        "Account", {"account_number": account_number, "company": company}
    )

    if not account_head:
        account_head = frappe.db.get_value(
            "Account",
            {
                "account_name": ["like", f"%{backup_name}%"],
                "company": company,
                "is_group": 0,
            },
        )

    if not account_head:
        frappe.logger().error(
            f"找不到科目: 公司 {company}, 科目编号 {account_number} 或名称 {backup_name}"
        )
        return (False, None)

    # 3. 修正科目类型
    if frappe.db.get_value("Account", account_head, "account_type") != "Tax":
        frappe.db.set_value(
            "Account", account_head, "account_type", "Tax", update_modified=False
        )

    # 4. 确定成本中心
    cost_center = frappe.db.get_value("Company", company, "cost_center")

    if not cost_center:
        cost_center = frappe.db.get_value(
            "Cost Center",
            {
                "company": company,
                "is_group": 1,
                "parent_cost_center": ["is", "not set"],
            },
            "name",
        )
        if not cost_center:
            cost_center = frappe.db.get_value(
                "Cost Center", {"company": company}, "name"
            )

    # 5. 创建新模板
    doc = frappe.new_doc(doctype)
    doc.title = title
    doc.company = company
    doc.is_default = is_default
    doc.set("taxes", [])

    # 6. 插入税率行
    doc.append(
        "taxes",
        {
            "charge_type": "On Net Total",
            "account_head": account_head,
            "rate": rate,
            "description": f"增值税 {rate}%",
            "cost_center": cost_center,
        },
    )

    doc.flags.ignore_permissions = True
    doc.save(ignore_version=True)
    frappe.db.commit()
    
    frappe.logger().info(f"成功创建税费模板: {title} (公司: {company})")
    return (True, doc.name)


def create_standard_taxes(company_name):
    """
    创建标准的中国增值税税费模板
    
    Args:
        company_name: 公司名称
    
    Returns:
        dict: 创建结果统计
    """
    tax_configs = [
        {"title": "13%", "rate": 13.0, "is_default": 1},
        {"title": "9%", "rate": 9.0, "is_default": 0},
        {"title": "6%", "rate": 6.0, "is_default": 0},
        {"title": "3%", "rate": 3.0, "is_default": 0},
        {"title": "1%", "rate": 1.0, "is_default": 0},
    ]

    created_count = 0
    skipped_count = 0
    error_count = 0
    created_templates = []
    skipped_templates = []

    for item in tax_configs:
        # 销项模板
        created, template_name = _make_idempotent_template(
            company_name,
            "Sales Taxes and Charges Template",
            f"中国增值税 - {item['title']} (销项)",
            "22210108",  # 销项编号
            "销项税额",  # 备份名称
            item["rate"],
            item["is_default"],
        )
        
        if created:
            created_count += 1
            created_templates.append(f"中国增值税 - {item['title']} (销项)")
        elif template_name:
            skipped_count += 1
            skipped_templates.append(f"中国增值税 - {item['title']} (销项)")
        else:
            error_count += 1

        # 进项模板
        created, template_name = _make_idempotent_template(
            company_name,
            "Purchase Taxes and Charges Template",
            f"中国增值税 - {item['title']} (进项)",
            "22210101",  # 进项编号
            "进项税额",  # 备份名称
            item["rate"],
            item["is_default"],
        )
        
        if created:
            created_count += 1
            created_templates.append(f"中国增值税 - {item['title']} (进项)")
        elif template_name:
            skipped_count += 1
            skipped_templates.append(f"中国增值税 - {item['title']} (进项)")
        else:
            error_count += 1

    return {
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count,
        "created_templates": created_templates,
        "skipped_templates": skipped_templates
    }


@frappe.whitelist()
def initialize_tax_templates(company):
    """
    初始化公司的进销项税费模板
    
    功能：
    1. 删除系统默认创建的 China Tax 模板
    2. 创建标准的中国增值税税费模板（跳过已存在的）
    
    Args:
        company: 公司名称
    
    Returns:
        dict: 设置结果，包含成功创建的模板数量和详细信息
    """
    try:
        # 验证公司是否存在
        if not frappe.db.exists("Company", company):
            return {
                "success": False,
                "message": _("公司 {0} 不存在").format(company),
                "count": 0,
                "details": {}
            }
        
        # 记录开始执行
        frappe.logger().info(
            f"开始为 {company} 初始化进销项税费模板"
        )
        
        # 1. 删除系统默认的 China Tax 模板
        delete_result = _delete_default_china_tax_templates(company)
        
        # 2. 创建标准的税费模板
        create_result = create_standard_taxes(company)
        
        # 3. 查询最终的模板数量
        sales_templates = frappe.db.get_all(
            "Sales Taxes and Charges Template",
            filters={"company": company, "title": ["like", "中国增值税%"]},
            fields=["name", "title"]
        )
        purchase_templates = frappe.db.get_all(
            "Purchase Taxes and Charges Template",
            filters={"company": company, "title": ["like", "中国增值税%"]},
            fields=["name", "title"]
        )
        
        total_count = len(sales_templates) + len(purchase_templates)
        
        # 构建消息
        message_parts = []
        
        if delete_result["count"] > 0:
            message_parts.append(
                _("删除系统默认模板 {0} 个").format(delete_result["count"])
            )
        
        if create_result["created"] > 0:
            message_parts.append(
                _("新建模板 {0} 个").format(create_result["created"])
            )
        
        if create_result["skipped"] > 0:
            message_parts.append(
                _("跳过已存在模板 {0} 个").format(create_result["skipped"])
            )
        
        if create_result["errors"] > 0:
            message_parts.append(
                _("创建失败 {0} 个").format(create_result["errors"])
            )
        
        if not message_parts:
            message = _("未执行任何操作")
        else:
            message = "，".join(message_parts)
        
        message += _("（当前共有 {0} 个税费模板）").format(total_count)
        
        return {
            "success": True,
            "message": message,
            "count": total_count,
            "details": {
                "deleted": delete_result,
                "created": create_result["created"],
                "skipped": create_result["skipped"],
                "errors": create_result["errors"],
                "sales_templates": [t["title"] for t in sales_templates],
                "purchase_templates": [t["title"] for t in purchase_templates],
                "created_templates": create_result["created_templates"],
                "skipped_templates": create_result["skipped_templates"]
            }
        }
            
    except Exception as e:
        frappe.log_error(
            f"初始化税费模板时出错: {str(e)}\n公司: {company}",
            f"初始化税费模板失败 - {company}"
        )
        return {
            "success": False,
            "message": _("初始化税费模板时出现错误: {0}").format(str(e)),
            "count": 0,
            "details": {}
        }


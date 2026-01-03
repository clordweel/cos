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
    company, doctype, title, account_name, backup_name, rate, is_default
):
    """
    创建或更新税费模板（幂等操作）
    如果模板已存在，则跳过创建
    
    Args:
        company: 公司名称
        doctype: 模板类型（Sales Taxes and Charges Template 或 Purchase Taxes and Charges Template）
        title: 模板标题
        account_name: 科目名称（从公司文档的自定义字段获取）
        backup_name: 备用科目名称（用于错误提示）
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

    # 1. 先验证传入的科目名称是否有效
    account_head = account_name
    
    # 验证科目是否存在且属于该公司（直接使用公司过滤器查询）
    if account_head:
        # 直接查询该公司下的科目，避免查询到其他公司的科目
        account_exists = frappe.db.exists("Account", {"name": account_head, "company": company})
        if not account_exists:
            # 如果按名称和公司查询不到，可能是科目名称或ID不正确
            # 检查是否是科目名称而不是ID，尝试通过名称查找
            account_by_name = frappe.db.get_value(
                "Account",
                {"account_name": account_head, "company": company, "is_group": 0},
                "name"
            )
            if account_by_name:
                account_head = account_by_name
            else:
                # 检查该科目是否存在（可能属于其他公司）
                account_exists_anywhere = frappe.db.exists("Account", account_head)
                if account_exists_anywhere:
                    account_company = frappe.db.get_value("Account", account_head, "company")
                    error_msg = f"科目 {account_head} 不属于公司 {company}（属于公司: {account_company}）。请检查公司文档中的 {backup_name} 字段是否正确设置。"
                else:
                    error_msg = f"科目不存在: {account_head} (公司: {company})。请检查公司文档中的 {backup_name} 字段是否正确设置。"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company}")
                account_head = None

    if not account_head:
        error_msg = f"找不到科目: 公司 {company}, 科目名称 {backup_name}。请检查公司文档中的 {backup_name} 字段是否正确设置，确保选择的科目属于该公司。"
        frappe.log_error(error_msg, f"税费模板创建失败 - {company}")
        return (False, None)

    # 2. 检查模板是否已存在
    existing_name = frappe.db.get_value(
        doctype, {"title": title, "company": company}
    )
    
    # 如果已存在，检查科目是否需要更新
    if existing_name:
        existing_doc = frappe.get_doc(doctype, existing_name)
        # 检查模板中的科目是否与当前科目一致
        needs_update = False
        
        # 如果模板中没有税行，或者税行数量不为1，需要更新
        if not existing_doc.taxes or len(existing_doc.taxes) != 1:
            needs_update = True
        else:
            # 检查第一个（也是唯一的）税行的科目和税率
            tax_row = existing_doc.taxes[0]
            if tax_row.account_head != account_head or tax_row.rate != rate:
                needs_update = True
        
        if needs_update:
            # 更新模板中的科目和税率
            try:
                existing_doc.set("taxes", [])
                existing_doc.append(
                    "taxes",
                    {
                        "charge_type": "On Net Total",
                        "account_head": account_head,
                        "rate": rate,
                        "description": f"增值税 {rate}%",
                        "cost_center": frappe.db.get_value("Company", company, "cost_center") or 
                                       frappe.db.get_value("Cost Center", {"company": company}, "name"),
                    },
                )
                existing_doc.flags.ignore_permissions = True
                existing_doc.save(ignore_version=True)
                frappe.db.commit()
                frappe.logger().info(
                    f"已更新模板: {title} (公司: {company})，科目: {account_head}，税率: {rate}%"
                )
                return (True, existing_name)
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                error_msg = f"更新模板失败: {title} (公司: {company})\n科目: {account_head}\n税率: {rate}%\n错误: {str(e)}\n{error_detail}"
                frappe.log_error(error_msg, f"税费模板更新失败 - {company}")
                frappe.db.rollback()
                return (False, None)
        else:
            frappe.logger().info(
                f"模板已存在且无需更新: {title} (公司: {company})，科目: {account_head}，税率: {rate}%"
            )
            return (False, existing_name)

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
    try:
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
        
        success_msg = f"成功创建税费模板: {title} (公司: {company})，科目: {account_head}，税率: {rate}%"
        frappe.logger().info(success_msg)
        return (True, doc.name)
    except Exception as e:
        import traceback
        error_msg = f"创建税费模板失败: {title} (公司: {company}), 错误: {str(e)}\n{traceback.format_exc()}"
        frappe.log_error(error_msg, f"税费模板创建失败 - {company}")
        frappe.db.rollback()
        return (False, None)


def create_standard_taxes(company_name):
    """
    创建标准的中国增值税税费模板
    使用公司文档中的自定义字段获取进销项税科目
    
    Args:
        company_name: 公司名称
    
    Returns:
        dict: 创建结果统计
    """
    # 从公司文档获取进销项税科目
    company_doc = frappe.get_cached_doc("Company", company_name)
    sales_account = company_doc.get("custom_selling_tax_account")
    purchase_account = company_doc.get("custom_buying_tax_account")
    
    if not sales_account or not purchase_account:
        missing = []
        missing_fields = []
        if not sales_account:
            missing.append(_("销售税科目 (Selling Tax Account)"))
            missing_fields.append("custom_selling_tax_account")
        if not purchase_account:
            missing.append(_("采购税科目 (Buying Tax Account)"))
            missing_fields.append("custom_buying_tax_account")
        
        error_message = _("公司 {0} 未设置税费科目字段，请在公司文档中设置：{1}").format(
            company_name, "、".join(missing)
        )
        frappe.log_error(
            f"公司 {company_name} 缺少税费科目字段: {', '.join(missing_fields)}. {error_message}",
            f"税费模板初始化失败 - {company_name}"
        )
        return {
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "created_templates": [],
            "skipped_templates": [],
            "error_message": error_message,
            "missing_fields": missing_fields
        }
    
    # 验证科目是否属于当前公司
    invalid_accounts = []
    if sales_account:
        account_company = frappe.db.get_value("Account", sales_account, "company")
        if account_company != company_name:
            invalid_accounts.append({
                "field": "custom_selling_tax_account",
                "account": sales_account,
                "belongs_to": account_company,
                "name": _("销售税科目 (Selling Tax Account)")
            })
    
    if purchase_account:
        account_company = frappe.db.get_value("Account", purchase_account, "company")
        if account_company != company_name:
            invalid_accounts.append({
                "field": "custom_buying_tax_account",
                "account": purchase_account,
                "belongs_to": account_company,
                "name": _("采购税科目 (Buying Tax Account)")
            })
    
    if invalid_accounts:
        error_details = []
        for item in invalid_accounts:
            error_details.append(
                _("{0} 设置的科目 {1} 不属于当前公司（属于公司: {2}）").format(
                    item["name"], item["account"], item["belongs_to"]
                )
            )
        error_message = _("公司 {0} 的税费科目字段设置有误：{1}。请在公司文档中重新选择属于该公司的科目。").format(
            company_name, "；".join(error_details)
        )
        frappe.log_error(
            error_message,
            f"税费模板初始化失败 - {company_name}"
        )
        return {
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "created_templates": [],
            "skipped_templates": [],
            "error_message": error_message,
            "invalid_accounts": invalid_accounts
        }
    
    tax_configs = [
        {"title": "13%", "rate": 13.0, "is_default": 1},
        {"title": "9%", "rate": 9.0, "is_default": 0},
        {"title": "6%", "rate": 6.0, "is_default": 0},
        {"title": "3%", "rate": 3.0, "is_default": 0},
        {"title": "1%", "rate": 1.0, "is_default": 0},
    ]

    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    created_templates = []
    updated_templates = []
    skipped_templates = []

    for item in tax_configs:
        # 销项模板
        template_title = f"中国增值税 - {item['title']} (销项)"
        # 先检查模板是否已存在
        existing_sales = frappe.db.get_value(
            "Sales Taxes and Charges Template",
            {"title": template_title, "company": company_name}
        )
        
        created_or_updated, template_name = _make_idempotent_template(
            company_name,
            "Sales Taxes and Charges Template",
            template_title,
            sales_account,  # 从公司文档获取的销项科目
            "销项税额",  # 备份名称（用于错误提示）
            item["rate"],
            item["is_default"],
        )
        
        if created_or_updated and template_name:
            if existing_sales:
                # 如果调用前已存在，说明是更新
                updated_count += 1
                updated_templates.append(template_title)
            else:
                # 如果调用前不存在，说明是新建
                created_count += 1
                created_templates.append(template_title)
        elif template_name:
            # template_name 存在但 created_or_updated 为 False，说明模板已存在且无需更新
            skipped_count += 1
            skipped_templates.append(template_title)
        else:
            # template_name 为 None，说明创建失败或科目验证失败
            error_count += 1
            # 检查是否是科目验证失败
            if not sales_account:
                error_msg = f"创建模板失败: {template_title} (公司: {company_name}) - 缺少销售税科目 (custom_selling_tax_account)"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")
            elif sales_account and not frappe.db.exists("Account", sales_account):
                error_msg = f"创建模板失败: {template_title} (公司: {company_name}) - 销售税科目 {sales_account} 不存在"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")
            else:
                error_msg = f"创建/更新模板失败: {template_title} (公司: {company_name})"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")

        # 进项模板
        template_title = f"中国增值税 - {item['title']} (进项)"
        # 先检查模板是否已存在
        existing_purchase = frappe.db.get_value(
            "Purchase Taxes and Charges Template",
            {"title": template_title, "company": company_name}
        )
        
        created_or_updated, template_name = _make_idempotent_template(
            company_name,
            "Purchase Taxes and Charges Template",
            template_title,
            purchase_account,  # 从公司文档获取的进项科目
            "进项税额",  # 备份名称（用于错误提示）
            item["rate"],
            item["is_default"],
        )
        
        if created_or_updated and template_name:
            if existing_purchase:
                # 如果调用前已存在，说明是更新
                updated_count += 1
                updated_templates.append(template_title)
            else:
                # 如果调用前不存在，说明是新建
                created_count += 1
                created_templates.append(template_title)
        elif template_name:
            # template_name 存在但 created_or_updated 为 False，说明模板已存在且无需更新
            skipped_count += 1
            skipped_templates.append(template_title)
        else:
            # template_name 为 None，说明创建失败或科目验证失败
            error_count += 1
            # 检查是否是科目验证失败
            if not purchase_account:
                error_msg = f"创建模板失败: {template_title} (公司: {company_name}) - 缺少采购税科目 (custom_buying_tax_account)"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")
            elif purchase_account and not frappe.db.exists("Account", purchase_account):
                error_msg = f"创建模板失败: {template_title} (公司: {company_name}) - 采购税科目 {purchase_account} 不存在"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")
            else:
                error_msg = f"创建/更新模板失败: {template_title} (公司: {company_name})"
                frappe.log_error(error_msg, f"税费模板创建失败 - {company_name}")

    return {
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": error_count,
        "created_templates": created_templates,
        "updated_templates": updated_templates,
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
        
        # 检查是否有科目字段未设置或科目不属于当前公司的错误
        if create_result.get("error_message"):
            return {
                "success": False,
                "message": create_result["error_message"],
                "count": 0,
                "details": {
                    "deleted": delete_result,
                    "missing_fields": create_result.get("missing_fields", []),
                    "invalid_accounts": create_result.get("invalid_accounts", [])
                }
            }
        
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
            error_msg = _("创建失败 {0} 个").format(create_result["errors"])
            # 如果有科目字段缺失，添加提示
            if create_result.get("missing_fields"):
                error_msg += _("（可能原因：公司缺少税费科目字段设置）")
            message_parts.append(error_msg)
        
        if not message_parts:
            message = _("未执行任何操作")
        else:
            message = "，".join(message_parts)
        
        message += _("（当前共有 {0} 个税费模板）").format(total_count)
        
        # 如果有错误，添加提示信息
        if create_result["errors"] > 0:
            message += _("\n提示：请检查错误日志以获取详细信息，或确认公司文档中的税费科目字段是否正确设置。")
        
        return {
            "success": True,
            "message": message,
            "count": total_count,
            "details": {
                "deleted": delete_result,
                "created": create_result["created"],
                "updated": create_result.get("updated", 0),
                "skipped": create_result["skipped"],
                "errors": create_result["errors"],
                "sales_templates": [t["title"] for t in sales_templates],
                "purchase_templates": [t["title"] for t in purchase_templates],
                "created_templates": create_result["created_templates"],
                "updated_templates": create_result.get("updated_templates", []),
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


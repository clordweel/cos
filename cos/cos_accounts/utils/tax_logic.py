import frappe
from frappe import _
from frappe.utils import flt


def update_item_tax_data(doc, method=None):
    """
    更新物料税率逻辑：增加多公司适配和科目存在性筛选
    """
    if not doc.item_group:
        frappe.log_error(
            f"Item {doc.name} has no item_group, skipping tax update",
            "Tax Update Warning"
        )
        return False

    tax_rate = get_tax_rate_hierarchy(doc.item_group)
    if tax_rate is None:
        frappe.log_error(
            f"Item {doc.name} (item_group: {doc.item_group}) has no tax rate in hierarchy",
            "Tax Update Warning"
        )
        return False

    # 获取所有非集团公司
    companies = frappe.get_all("Company", filters={"is_group": 0})
    if not companies:
        frappe.log_error(
            f"No companies found for tax template creation",
            "Tax Update Warning"
        )
        return False

    target_templates = []
    missing_companies = []
    for c in companies:
        try:
            template_name = ensure_combined_tax_template(c.name, tax_rate)
            if template_name:
                target_templates.append(template_name)
        except frappe.ValidationError as e:
            # 捕获字段缺失的错误，记录但继续处理其他公司
            missing_companies.append(f"{c.name}: {str(e)}")
            frappe.log_error(
                f"Company {c.name} missing tax account fields: {str(e)}",
                "Tax Update Warning"
            )

    # 如果没有找到任何模板，记录错误
    if not target_templates:
        error_msg = f"Item {doc.name} (item_group: {doc.item_group}, rate: {tax_rate}%): "
        error_msg += f"No tax templates found for any company. Companies checked: {[c.name for c in companies]}"
        if missing_companies:
            error_msg += f"\nMissing account fields: {'; '.join(missing_companies)}"
        frappe.log_error(error_msg, "Tax Update Error")
        return False

    # 性能优化：检查当前物料的税率表是否已符合目标
    current_templates = [d.item_tax_template for d in doc.get("taxes")]

    if set(target_templates) == set(current_templates) and len(target_templates) == len(
        current_templates
    ):
        return False

    # 执行更新
    doc.set("taxes", [])
    for t_name in target_templates:
        doc.append(
            "taxes",
            {
                "item_tax_template": t_name,
                "tax_category": "",
            },
        )
    return True


def ensure_combined_tax_template(company, rate):
    """
    改进后的模板生成：严格筛选公司科目
    使用公司文档中的自定义字段获取进销项税科目
    """
    title = f"中国增值税 {rate}% ({company})"

    # 1. 检查是否存在该模板
    existing_name = frappe.db.get_value(
        "Item Tax Template", {"title": title, "company": company}, "name"
    )

    # 2. 核心改进：从公司文档获取进销项税科目
    company_doc = frappe.get_cached_doc("Company", company)
    sales_account = company_doc.get("custom_selling_tax_account")
    purchase_account = company_doc.get("custom_buying_tax_account")

    # 如果该公司不具备这两个科目，抛出错误提示用户
    if not sales_account or not purchase_account:
        missing = []
        missing_fields = []
        if not sales_account:
            missing.append(_("销售税科目 (Selling Tax Account)"))
            missing_fields.append("custom_selling_tax_account")
        if not purchase_account:
            missing.append(_("采购税科目 (Buying Tax Account)"))
            missing_fields.append("custom_buying_tax_account")
        
        error_msg = _("公司 {0} 未设置税费科目字段，请在公司文档中设置：{1}").format(
            company, "、".join(missing)
        )
        frappe.log_error(
            f"Company {company} missing tax accounts: {', '.join(missing_fields)}. {error_msg}",
            "Tax Template Creation Warning"
        )
        frappe.throw(error_msg, title=_("税费科目字段未设置"))

    # 3. 校验科目类型（防止报错"科目类型须为税项"）
    for acc in [sales_account, purchase_account]:
        acc_type = frappe.db.get_value("Account", acc, "account_type")
        if acc_type not in ["Tax", "Income", "Expense"]:
            # 只有在确定的情况下才修正
            frappe.db.set_value("Account", acc, "account_type", "Tax")

    if existing_name:
        update_existing_template(existing_name, sales_account, purchase_account, rate)
        return existing_name

    # 4. 创建新模板
    try:
        new_template = frappe.get_doc(
            {
                "doctype": "Item Tax Template",
                "title": title,
                "company": company,
                "taxes": [
                    {"tax_type": sales_account, "tax_rate": rate},
                    {"tax_type": purchase_account, "tax_rate": rate},
                ],
            }
        )
        new_template.insert(ignore_permissions=True, ignore_if_duplicate=True)
        return new_template.name
    except Exception as e:
        frappe.log_error(
            f"Company {company} template creation failed: {str(e)}",
            "Tax Template Creation Error"
        )
        return None


def update_existing_template(template_name, sales_account, purchase_account, rate):
    """
    更新现有模板，确保科目准确
    如果科目已更改，则更新模板中的科目
    """
    t_doc = frappe.get_doc("Item Tax Template", template_name)
    accounts_in_tpl = {d.tax_type: d for d in t_doc.taxes}
    target_accounts = {sales_account, purchase_account}

    updated = False
    
    # 检查是否需要更新税率
    for tax_row in t_doc.taxes:
        if tax_row.tax_type in target_accounts and tax_row.tax_rate != rate:
            tax_row.tax_rate = rate
            updated = True
    
    # 检查是否需要添加缺失的科目
    for acc in [sales_account, purchase_account]:
        if acc and acc not in accounts_in_tpl:
            t_doc.append("taxes", {"tax_type": acc, "tax_rate": rate})
            updated = True
    
    # 检查是否需要移除不再使用的科目（可选，根据业务需求决定）
    # 这里我们只更新，不移除，因为可能有其他用途
    
    if updated:
        t_doc.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"已更新模板 {template_name} 的科目和税率")


def get_tax_rate_hierarchy(group_name):
    """层级获取税率"""
    rate = frappe.db.get_value("Item Group", group_name, "custom_standard_tax_rate")
    if rate is not None:
        return flt(rate)

    parent = frappe.db.get_value("Item Group", group_name, "parent_item_group")
    if parent and parent != "All Item Groups":
        return get_tax_rate_hierarchy(parent)
    return None


def daily_tax_audit():
    """计划任务：高性能巡查"""
    items = frappe.get_all("Item", fields=["name"])
    updated_count = 0

    for i in items:
        doc = frappe.get_doc("Item", i.name)
        if update_item_tax_data(doc):
            doc.save(ignore_permissions=True)
            updated_count += 1

    if updated_count > 0:
        frappe.logger().info(f"Tax Audit: Updated {updated_count} items.")

"""
物料税费模板逻辑（COS 二开）

- 统一名称格式：中国增值税 {rate}% ({company})
- 税率展示：整数不保留小数（13% 非 13.0%），小数保留一位（6.5%）
"""
import frappe
from frappe import _
from frappe.utils import flt

# 物料税费模板 title 前缀，便于筛选与清理
ITEM_TAX_TEMPLATE_TITLE_PREFIX = "中国增值税"


def _format_tax_rate_display(rate):
    """税率展示：整数去尾零（13 非 13.0），小数保留一位（6.5）。"""
    r = flt(rate, 1)
    if r == int(r):
        return str(int(r))
    return str(r)


def _format_item_tax_template_title(company, rate):
    """物料税费模板 title 标准格式：中国增值税 {rate}% ({company})。"""
    rate_str = _format_tax_rate_display(rate)
    return f"{ITEM_TAX_TEMPLATE_TITLE_PREFIX} {rate_str}% ({company})"


def _find_existing_item_tax_template(company, rate):
    """
    查找已存在的物料税费模板，兼容新旧 title 格式。
    新格式：中国增值税 13% (公司)
    旧格式：中国增值税 13.0% (公司)
    """
    title_new = _format_item_tax_template_title(company, rate)
    existing = frappe.db.get_value(
        "Item Tax Template", {"title": title_new, "company": company}, "name"
    )
    if existing:
        return existing
    # 兼容旧格式（如 13.0%）
    title_old = f"{ITEM_TAX_TEMPLATE_TITLE_PREFIX} {flt(rate, 1)}% ({company})"
    if title_old != title_new:
        existing = frappe.db.get_value(
            "Item Tax Template", {"title": title_old, "company": company}, "name"
        )
    return existing


def update_item_tax_data(doc, method=None, company=None):
    """
    更新物料税率逻辑：增加多公司适配和科目存在性筛选

    :param doc: Item 文档
    :param method: 保留（doc_events 调用时传入）
    :param company: 可选，仅处理指定公司；为 None 时处理所有非集团公司
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

    # 获取目标公司列表
    if company:
        if not frappe.db.exists("Company", company):
            frappe.logger().warning(f"Company {company} not found")
            return False
        companies = [{"name": company}]
    else:
        companies = frappe.get_all("Company", filters={"is_group": 0})

    if not companies:
        frappe.log_error(
            f"No companies found for tax template creation",
            "Tax Update Warning"
        )
        return False

    target_templates = []
    skipped_companies = []
    for c in companies:
        template_name = ensure_combined_tax_template(c.name, tax_rate)
        if template_name:
            target_templates.append(template_name)
        else:
            skipped_companies.append(c.name)

    if not target_templates:
        warning_msg = f"Item {doc.name} (item_group: {doc.item_group}, rate: {tax_rate}%): "
        warning_msg += f"No tax templates found. Companies checked: {[c.name for c in companies]}"
        if skipped_companies:
            warning_msg += f"\nSkipped (missing tax account fields): {', '.join(skipped_companies)}"
        frappe.logger().warning(warning_msg)
        return False

    current_templates = [d.item_tax_template for d in doc.get("taxes")]

    if company:
        # 仅当前公司：合并模式，确保目标模板在列表中
        if target_templates[0] in current_templates:
            return False
        doc.append(
            "taxes",
            {"item_tax_template": target_templates[0], "tax_category": ""},
        )
        return True

    # 全部公司：替换模式
    if set(target_templates) == set(current_templates) and len(target_templates) == len(
        current_templates
    ):
        return False
    doc.set("taxes", [])
    for t_name in target_templates:
        doc.append(
            "taxes",
            {"item_tax_template": t_name, "tax_category": ""},
        )
    return True


def ensure_combined_tax_template(company, rate):
    """
    创建或获取物料税费模板（销项+进项合并）。

    名称格式：中国增值税 {rate}% ({company})
    税率展示：整数不保留小数（13%），小数保留一位（6.5%）
    """
    title = _format_item_tax_template_title(company, rate)

    # 1. 检查是否存在该模板（兼容新旧格式）
    existing_name = _find_existing_item_tax_template(company, rate)

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
        
        warning_msg = _("公司 {0} 未设置税费科目字段，请在公司文档中设置：{1}").format(
            company, "、".join(missing)
        )
        frappe.logger().warning(
            f"Company {company} missing tax accounts: {', '.join(missing_fields)}. {warning_msg}"
        )
        # 跳过该公司的模板创建
        return None

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

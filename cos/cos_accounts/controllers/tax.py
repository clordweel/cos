import frappe
from frappe import _
from cos.cos_accounts.utils.tax_logic import (
    update_item_tax_data,
    get_tax_rate_hierarchy,
    ensure_combined_tax_template,
    _account_exists_and_belongs_to_company,
)


# --- 供按钮调用的函数保持不变，但内部逻辑已更新 ---
@frappe.whitelist()
def sync_group_taxes_to_items(item_group):
    """
    同步物料组的税率到所有子物料
    """
    try:
        group_info = frappe.db.get_value(
            "Item Group", item_group, ["lft", "rgt"], as_dict=True
        )
        if not group_info:
            return {"message": f"Item Group {item_group} not found"}

        descendants = frappe.get_all(
            "Item Group",
            filters={"lft": (">=", group_info.lft), "rgt": ("<=", group_info.rgt)},
        )
        items = frappe.get_all(
            "Item", filters={"item_group": ("in", [d.name for d in descendants])}
        )

        count = 0
        updated_count = 0
        error_count = 0
        errors = []
        missing_account_warnings = []
        
        for i in items:
            try:
                doc = frappe.get_doc("Item", i.name)
                # 只在税率数据需要更新时才保存
                if update_item_tax_data(doc):
                    doc.save(ignore_permissions=True)
                    updated_count += 1
                count += 1
                if count % 100 == 0:
                    frappe.db.commit()
            except frappe.ValidationError as e:
                # 如果是字段缺失错误，记录警告但继续处理
                if "税费科目字段未设置" in str(e):
                    missing_account_warnings.append(f"Item {i.name}: {str(e)}")
                else:
                    error_count += 1
                    error_msg = f"Item {i.name}: {str(e)}"
                    errors.append(error_msg)
                frappe.log_error(f"Error updating tax for item {i.name}: {str(e)}")
            except Exception as e:
                error_count += 1
                error_msg = f"Item {i.name}: {str(e)}"
                errors.append(error_msg)
                frappe.log_error(f"Error updating tax for item {i.name}: {str(e)}")
                # 继续处理其他物料，不中断整个流程

        frappe.db.commit()
        
        message = f"处理了 {count} 个物料，成功更新 {updated_count} 个物料的税率模板"
        if missing_account_warnings:
            message += f"\n警告：{len(missing_account_warnings)} 个物料因公司缺少税费科目字段而跳过"
            if len(missing_account_warnings) <= 3:
                message += "：" + "；".join(missing_account_warnings[:3])
        if error_count > 0:
            message += f"\n错误：{error_count} 个物料更新失败"
            if len(errors) <= 5:  # 只显示前5个错误
                message += "：" + "；".join(errors[:5])
        
        return {"message": message, "updated": updated_count, "total": count, "errors": error_count}
    except Exception as e:
        frappe.log_error(f"Error in sync_group_taxes_to_items: {str(e)}")
        frappe.throw(f"Failed to sync tax rates: {str(e)}")


@frappe.whitelist()
def bulk_cleanup_tax_templates(keyword="(Output)"):
    """
    修正版：一键清理所有标题包含特定关键字的旧版模板。
    Item Tax 表在数据库中同时服务于 Item 和 Item Group 的税率关联。
    """
    # 查找匹配的模板
    templates = frappe.get_all(
        "Item Tax Template", filters=[["title", "like", f"%{keyword}%"]]
    )

    count = 0
    for t in templates:
        t_name = t.name

        # 1. 核心修复：清理所有引用该模板的子表行
        # 在 ERPNext 中，Item 和 Item Group 的税率子表都存储在 tabItem Tax 表中
        # parenttype 字段会区分它是属于 Item 还是 Item Group
        frappe.db.delete("Item Tax", {"item_tax_template": t_name})

        # 2. 删除模板文档本身
        # 使用 ignore_missing 以防万一某些文档已被手动删除
        frappe.delete_doc("Item Tax Template", t_name, ignore_missing=True)
        count += 1

    frappe.db.commit()
    return {"message": f"Successfully cleaned up {count} legacy templates and all (Item/Item Group) associated references."}


@frappe.whitelist()
def update_single_item_tax(item_code, company=None, tax_rate=None):
    """
    手动更新单个物料的税率模板

    :param item_code: 物料编码
    :param company: 可选，仅更新/创建指定公司的税费模板；为 None 时更新所有公司
    :param tax_rate: 可选，指定税率；为 None 时从物料组层级获取
    """
    try:
        doc = frappe.get_doc("Item", item_code)
        updated = update_item_tax_data(doc, company=company, tax_rate=tax_rate)
        if updated:
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {"message": f"成功更新物料 {item_code} 的税率模板"}
        else:
            return {"message": f"物料 {item_code} 的税率模板无需更新"}
    except frappe.ValidationError as e:
        # 如果是字段缺失错误，记录警告但不抛出异常
        warning_msg = f"更新物料 {item_code} 的税率模板时：{str(e)}"
        frappe.logger().warning(warning_msg)
        return {"message": warning_msg, "warning": True}
    except Exception as e:
        frappe.log_error(f"Error updating tax for item {item_code}: {str(e)}")
        frappe.throw(f"更新税率模板失败: {str(e)}")


@frappe.whitelist()
def diagnose_item_tax(item_code):
    """
    诊断物料的税率设置问题
    """
    try:
        doc = frappe.get_doc("Item", item_code)
        result = {
            "item_code": item_code,
            "item_name": doc.item_name,
            "item_group": doc.item_group,
            "current_taxes": [{"template": d.item_tax_template, "category": d.tax_category} for d in doc.get("taxes")],
            "diagnosis": []
        }
        
        # 检查物料组
        if not doc.item_group:
            result["diagnosis"].append({
                "level": "error",
                "message": "物料没有设置物料组"
            })
            return result
        
        # 检查税率
        tax_rate = get_tax_rate_hierarchy(doc.item_group)
        if tax_rate is None:
            result["diagnosis"].append({
                "level": "error",
                "message": f"物料组 '{doc.item_group}' 及其父级都没有设置税率 (custom_standard_tax_rate)"
            })
            return result
        
        result["tax_rate"] = tax_rate
        result["diagnosis"].append({
            "level": "info",
            "message": f"找到税率: {tax_rate}%"
        })
        
        # 检查公司
        companies = frappe.get_all("Company", filters={"is_group": 0})
        if not companies:
            result["diagnosis"].append({
                "level": "error",
                "message": "系统中没有找到非集团公司"
            })
            return result
        
        result["companies"] = []
        target_templates = []
        
        for c in companies:
            company_info = {
                "name": c.name,
                "has_sales_account": False,
                "has_purchase_account": False,
                "template_created": False,
                "template_name": None
            }
            
            # 从公司文档获取科目
            company_doc = frappe.get_cached_doc("Company", c.name)
            sales_account = company_doc.get("custom_selling_tax_account")
            purchase_account = company_doc.get("custom_buying_tax_account")
            
            company_info["has_sales_account"] = bool(sales_account)
            company_info["has_purchase_account"] = bool(purchase_account)
            
            # 检查科目已设置但不存在或归属错误
            account_not_found = []
            if sales_account and not _account_exists_and_belongs_to_company(sales_account, c.name):
                account_not_found.append(f"销售税科目: {sales_account}")
            if purchase_account and not _account_exists_and_belongs_to_company(purchase_account, c.name):
                account_not_found.append(f"采购税科目: {purchase_account}")

            if account_not_found:
                company_info["account_not_found"] = account_not_found
                company_info["error_message"] = f"公司 {c.name} 所指科目不存在或不属于该公司：{'；'.join(account_not_found)}。请在公司文档中修正。"
            elif sales_account and purchase_account:
                template_name = ensure_combined_tax_template(c.name, tax_rate)
                if template_name:
                    company_info["template_created"] = True
                    company_info["template_name"] = template_name
                    target_templates.append(template_name)
            else:
                missing = []
                missing_fields = []
                if not sales_account:
                    missing.append("销售税科目 (Selling Tax Account)")
                    missing_fields.append("custom_selling_tax_account")
                if not purchase_account:
                    missing.append("采购税科目 (Buying Tax Account)")
                    missing_fields.append("custom_buying_tax_account")
                company_info["missing_accounts"] = missing
                company_info["missing_fields"] = missing_fields
                company_info["error_message"] = f"公司 {c.name} 未设置税费科目字段，请在公司文档中设置：{'、'.join(missing)}"
            
            result["companies"].append(company_info)
        
        result["target_templates"] = target_templates
        result["expected_taxes"] = [{"template": t, "category": ""} for t in target_templates]
        
        # 检查是否有公司缺少科目字段
        companies_with_missing_fields = [
            c for c in result["companies"]
            if c.get("missing_fields")
        ]
        if companies_with_missing_fields:
            missing_companies = [c["name"] for c in companies_with_missing_fields]
            result["diagnosis"].append({
                "level": "error",
                "message": f"以下公司未设置税费科目字段：{', '.join(missing_companies)}。请在公司文档中设置相应的科目字段（custom_selling_tax_account、custom_buying_tax_account）。"
            })

        # 检查是否有公司科目已设置但所指科目不存在
        companies_with_account_not_found = [
            c for c in result["companies"]
            if c.get("account_not_found")
        ]
        if companies_with_account_not_found:
            for c in companies_with_account_not_found:
                result["diagnosis"].append({
                    "level": "error",
                    "message": c.get("error_message", f"公司 {c['name']} 税费科目所指科目不存在或归属错误。")
                })
        
        # 比较当前和目标
        current_templates = [d.item_tax_template for d in doc.get("taxes")]
        has_company_issues = companies_with_missing_fields or companies_with_account_not_found
        if set(target_templates) != set(current_templates):
            if not has_company_issues:  # 只有在没有科目问题时才显示模板不匹配警告
                result["diagnosis"].append({
                    "level": "warning",
                    "message": f"物料的税率模板不匹配。当前: {current_templates}, 期望: {target_templates}"
                })
        else:
            if target_templates:  # 只有在有目标模板的情况下才显示成功消息
                result["diagnosis"].append({
                    "level": "success",
                    "message": "物料的税率模板设置正确"
                })
        
        return result
    except Exception as e:
        frappe.log_error(f"Error in diagnose_item_tax: {str(e)}")
        frappe.throw(f"诊断失败: {str(e)}")


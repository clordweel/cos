"""
公司默认值设置控制器
使用通用默认值加载工具来设置公司默认值
"""
import frappe
import os
from frappe import _
from cos.cos_accounts.utils.defaults_loader import (
    load_defaults_config,
    apply_defaults_to_doc
)


def _get_company_defaults_config_path():
    """获取公司默认值配置文件路径"""
    module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(module_path, "data", "company_defaults.json")


@frappe.whitelist()
def initialize_company_defaults(company, override_existing=0):
    """
    初始化公司的默认值（包括默认账户和其他默认字段）
    
    Args:
        company: 公司名称
        override_existing: 是否覆盖已有值（0=不覆盖，1=覆盖）
    
    Returns:
        dict: 设置结果，包含成功设置的字段数量和详细信息
    """
    try:
        company_doc = frappe.get_doc('Company', company)
        company_name = company_doc.name
        abbr = company_doc.abbr
        
        # 加载配置文件
        config_path = _get_company_defaults_config_path()
        defaults_config = load_defaults_config(config_path)
        
        if not defaults_config:
            return {
                "success": False,
                "message": _("无法加载默认值配置，请检查配置文件"),
                "count": 0,
                "details": {}
            }
        
        # 准备上下文信息
        context = {
            "company_name": company_name,
            "abbr": abbr
        }
        
        # 应用默认值（只填充，不保存）
        # override_existing: 0=跳过已有值，1=覆盖已有值
        # 确保参数是整数类型
        override_existing = int(override_existing) if override_existing is not None else 0
        skip_existing = not bool(override_existing)
        
        # 调试日志
        frappe.logger().debug(f"初始化默认值 - 公司: {company_name}, override_existing: {override_existing}, skip_existing: {skip_existing}")
        
        result = apply_defaults_to_doc(
            company_doc,
            defaults_config,
            context=context,
            skip_existing=skip_existing
        )
        
        # 不保存文档，只填充值到文档对象中，由用户决定是否保存
        
        # 构建返回消息
        # 通过解析配置判断账户字段
        from cos.cos_accounts.utils.defaults_loader import _parse_field_value
        
        account_fields = []
        for k in result["values_set"].keys():
            if k in defaults_config:
                field_type, actual_value = _parse_field_value(defaults_config[k])
                if field_type == "account":
                    account_fields.append(k)
        other_fields = [
            k for k in result["values_set"].keys()
            if k not in account_fields
        ]
        
        account_count = len(account_fields)
        other_count = len(other_fields)
        
        message_parts = []
        if account_count > 0:
            message_parts.append(_("成功设置 {0} 个默认账户字段").format(account_count))
        if other_count > 0:
            message_parts.append(_("成功设置 {0} 个其他默认字段").format(other_count))
        
        message = "，".join(message_parts) if message_parts else _("未设置任何字段")
        
        if result["not_found"]:
            message += _("\n未找到 {0} 个账户字段").format(len(result["not_found"]))
        
        if result["skipped"]:
            message += _("\n跳过 {0} 个已有值的字段").format(len(result["skipped"]))
        
        # 构建详细信息
        details = {
            "accounts_set": {
                k: frappe.db.get_value("Account", v, "account_name")
                for k, v in result["values_set"].items()
                if k in account_fields
            },
            "other_values_set": {
                k: v for k, v in result["values_set"].items()
                if k in other_fields
            },
            "accounts_not_found": result["not_found"],
            "skipped_fields": result["skipped"]
        }
        
        return {
            "success": True,
            "message": message,
            "count": len(result["values_set"]),
            "details": details,
            "values_to_set": result["values_set"]  # 返回要设置的值，供前端使用
        }
            
    except Exception as e:
        frappe.log_error(
            f"初始化公司默认值时出错: {str(e)}\n公司: {company}",
            f"初始化公司默认值失败 - {company}"
        )
        return {
            "success": False,
            "message": _("初始化默认值时出现错误: {0}").format(str(e)),
            "count": 0,
            "details": {}
        }

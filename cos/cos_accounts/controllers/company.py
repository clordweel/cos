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


def _get_data_directory():
    """获取数据目录路径"""
    module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(module_path, "data")


def _get_company_defaults_config_path(config_file=None):
    """
    获取公司默认值配置文件路径
    
    Args:
        config_file: 配置文件名，如果为None则使用默认文件
    
    Returns:
        str: 配置文件完整路径
    """
    data_dir = _get_data_directory()
    if config_file:
        return os.path.join(data_dir, config_file)
    return os.path.join(data_dir, "company_defaults.json")


@frappe.whitelist()
def get_available_config_files():
    """
    获取可用的配置文件列表
    仅系统管理员可以访问
    
    Returns:
        list: 配置文件列表，每个元素包含文件名和显示名称
    """
    # 权限检查：仅系统管理员
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("权限不足：只有系统管理员可以访问此功能"), frappe.PermissionError)
    
    try:
        data_dir = _get_data_directory()
        config_files = []
        
        # 调试日志
        frappe.logger().debug(f"扫描配置文件目录: {data_dir}")
        
        # 扫描 data 目录下所有 company_defaults*.json 文件
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.startswith("company_defaults") and filename.endswith(".json"):
                    filepath = os.path.join(data_dir, filename)
                    if os.path.isfile(filepath):
                        # 尝试从配置文件中读取 title
                        display_name = None
                        try:
                            config_data = load_defaults_config(filepath)
                            if config_data and "_meta" in config_data and "title" in config_data["_meta"]:
                                display_name = config_data["_meta"]["title"]
                        except Exception as e:
                            frappe.logger().debug(f"读取配置文件 {filename} 的元数据失败: {str(e)}")
                        
                        # 如果没有 title，使用文件名生成显示名称
                        if not display_name:
                            display_name = filename.replace(".json", "").replace("_", " ").title()
                            # 如果是默认文件，添加标记
                            if filename == "company_defaults.json":
                                display_name += " (默认)"
                        
                        config_files.append({
                            "filename": filename,
                            "display_name": display_name
                        })
                        frappe.logger().debug(f"找到配置文件: {filename}, 显示名称: {display_name}")
        
        # 按文件名排序，默认文件排在第一位
        config_files.sort(key=lambda x: (x["filename"] != "company_defaults.json", x["filename"]))
        
        frappe.logger().debug(f"返回 {len(config_files)} 个配置文件")
        
        # 如果没有找到任何配置文件，至少返回默认文件（如果存在）
        if not config_files:
            default_path = os.path.join(data_dir, "company_defaults.json")
            if os.path.exists(default_path):
                display_name = "Company Defaults (默认)"
                try:
                    config_data = load_defaults_config(default_path)
                    if config_data and "_meta" in config_data and "title" in config_data["_meta"]:
                        display_name = config_data["_meta"]["title"]
                except Exception:
                    pass
                config_files.append({
                    "filename": "company_defaults.json",
                    "display_name": display_name
                })
        
        return config_files
    except Exception as e:
        frappe.log_error(f"获取配置文件列表失败: {str(e)}\n目录: {data_dir}", "Get Config Files Error")
        frappe.throw(_("获取配置文件列表失败: {0}").format(str(e)))


@frappe.whitelist()
def initialize_company_defaults(company, override_existing=0, config_file=None):
    """
    初始化公司的默认值（包括默认账户和其他默认字段）
    仅系统管理员可以访问
    
    Args:
        company: 公司名称
        override_existing: 是否覆盖已有值（0=不覆盖，1=覆盖）
        config_file: 配置文件名，如果为None则使用默认文件
    
    Returns:
        dict: 设置结果，包含成功设置的字段数量和详细信息
    """
    # 权限检查：仅系统管理员
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("权限不足：只有系统管理员可以执行此操作"), frappe.PermissionError)
    
    try:
        company_doc = frappe.get_doc('Company', company)
        company_name = company_doc.name
        abbr = company_doc.abbr
        
        # 加载配置文件
        config_path = _get_company_defaults_config_path(config_file)
        defaults_config = load_defaults_config(config_path)
        
        # 移除 _meta 字段（如果存在），因为它不是配置数据
        if defaults_config and "_meta" in defaults_config:
            defaults_config = {k: v for k, v in defaults_config.items() if k != "_meta"}
        
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
        frappe.logger().debug(
            f"初始化默认值 - 公司: {company_name}, "
            f"配置文件: {config_file or 'company_defaults.json'}, "
            f"override_existing: {override_existing}, skip_existing: {skip_existing}"
        )
        
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

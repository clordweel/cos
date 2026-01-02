"""
通用默认值加载工具
支持从JSON配置文件加载并应用默认值到文档
如果值是数组，第一项为字段类型（如 "account"），第二项为值
如果值不是数组，直接作为普通值使用
"""
import frappe
import json
from typing import Dict, Any, Optional, Tuple, List


def load_defaults_config(config_file_path: str) -> Dict[str, Any]:
    """
    从JSON文件加载默认值配置
    
    Args:
        config_file_path: 配置文件路径
    
    Returns:
        dict: 配置字典，如果加载失败返回空字典
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        frappe.log_error(
            f"加载默认值配置失败: {str(e)}\n文件路径: {config_file_path}",
            "Defaults Config Load Error"
        )
        return {}


def find_account(company_name: str, abbr: str, account_name: str) -> Optional[str]:
    """
    查找账户
    
    Args:
        company_name: 公司名称
        abbr: 公司简称
        account_name: 账户名称
    
    Returns:
        str: 找到的账户名称，如果未找到返回 None
    """
    # 方法1: 通过 account_name 字段精确查找（账户名称，不包含编号和简称）
    account_filters = {
        "company": company_name,
        "account_name": account_name,
        "is_group": 0
    }
    account = frappe.db.get_value("Account", account_filters)
    
    # 方法2: 如果没找到，尝试通过 name 字段查找（完整名称格式: "账户编号 - 账户名称 - 公司简称"）
    if not account:
        account_name_with_abbr = f'{account_name} - {abbr}'
        account = frappe.db.sql("""
            SELECT name 
            FROM `tabAccount` 
            WHERE company = %s 
            AND is_group = 0 
            AND name LIKE %s
            LIMIT 1
        """, (company_name, f'%{account_name_with_abbr}'), as_dict=False)
        if account:
            account = account[0][0]
    
    # 方法3: 如果还是没找到，尝试查找组账户（某些字段允许使用组账户）
    if not account:
        account = frappe.db.get_value("Account", {
            "company": company_name,
            "account_name": account_name
        })
    
    return account


def _parse_field_value(field_value: Any) -> Tuple[str, Any]:
    """
    解析字段值，提取类型和实际值
    
    Args:
        field_value: 字段值（可能是数组或直接值）
    
    Returns:
        tuple: (字段类型, 实际值)
        字段类型: "account" 或其他类型，如果不是数组则返回 "value"
    """
    if isinstance(field_value, list) and len(field_value) >= 2:
        # 数组格式：[类型, 值]
        field_type = field_value[0]
        actual_value = field_value[1]
        return field_type, actual_value
    else:
        # 直接值格式
        return "value", field_value


def resolve_field_value(
    field_name: str,
    field_value: Any,
    context: Dict[str, Any]
) -> Tuple[Optional[Any], bool]:
    """
    解析字段值
    
    Args:
        field_name: 字段名称
        field_value: 字段值（可能是数组 [类型, 值] 或直接值）
        context: 上下文信息，如 company_name, abbr 等
    
    Returns:
        tuple: (解析后的值, 是否成功)
    """
    # 解析字段类型和实际值
    field_type, actual_value = _parse_field_value(field_value)
    
    if field_type == "account":
        # 账户类型：需要查找账户
        company_name = context.get("company_name")
        abbr = context.get("abbr")
        
        if not company_name or not abbr:
            return None, False
        
        if not isinstance(actual_value, str):
            return None, False
        
        account = find_account(company_name, abbr, actual_value)
        return account, account is not None
    else:
        # 普通值类型：直接使用
        return actual_value, True


def apply_defaults_to_doc(
    doc: Any,
    defaults_config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    将默认值应用到文档
    
    Args:
        doc: Frappe 文档对象
        defaults_config: 默认值配置字典 {field_name: value 或 [type, value]}
        context: 上下文信息（如 company_name, abbr 等）
        skip_existing: 是否跳过已有值的字段
    
    Returns:
        dict: 应用结果 {
            "values_set": {},      # 成功设置的字段
            "not_found": {},       # 未找到的字段（主要是账户字段）
            "skipped": []          # 跳过的字段（已有值）
        }
    """
    if context is None:
        context = {}
    
    values_set = {}
    not_found = {}
    skipped = []
    
    for field_name, field_value in defaults_config.items():
        # 检查字段是否存在（使用 getattr 和 meta 两种方式）
        if not (hasattr(doc, field_name) or field_name in doc.meta.get_fieldnames()):
            continue
        
        current_value = doc.get(field_name)
        
        # 解析字段类型和实际值
        field_type, actual_value = _parse_field_value(field_value)
        
        # 如果跳过已有值，且字段已有值
        if skip_existing:
            # 判断字段是否有值（非空、非None、非0/False）
            def has_value(val):
                """判断字段是否有实际值"""
                if val is None:
                    return False
                if isinstance(val, str):
                    return val.strip() != ""  # 空字符串视为无值
                if isinstance(val, (int, bool)):
                    return val != 0  # 0/False 视为无值
                return True  # 其他类型（如列表、字典等）视为有值
            
            # 对于账户字段，如果当前值已经是账户，跳过
            if field_type == "account":
                if has_value(current_value):
                    skipped.append(field_name)
                    continue
            else:
                # 对于普通值，如果当前值有值，跳过（避免覆盖用户设置）
                if has_value(current_value):
                    skipped.append(field_name)
                    continue
        
        # 解析字段值
        resolved_value, success = resolve_field_value(field_name, field_value, context)
        
        if success:
            # 对于普通值，即使 resolved_value 是 0 或 False，也应该设置
            if field_type == "account":
                if resolved_value is not None:
                    values_set[field_name] = resolved_value
                else:
                    # 记录未找到的账户字段
                    not_found[field_name] = actual_value
            else:
                # 普通值类型，直接设置（包括 0、False、空字符串等）
                values_set[field_name] = resolved_value
    
    # 应用值到文档
    if values_set:
        doc.update(values_set)
    
    return {
        "values_set": values_set,
        "not_found": not_found,
        "skipped": skipped
    }

__version__ = "0.0.1"

import os
import importlib
import frappe

# 模块级别的标志，确保补丁只加载一次
_patches_loaded = False


def _load_monkey_patches_once():
    """自动加载 monkey_patches 目录下的所有补丁文件（只加载一次）"""
    global _patches_loaded

    if _patches_loaded:
        return

    # 检查应用是否已安装（可选，如果数据库不可用则跳过检查）
    try:
        if frappe.db and not frappe.db.exists("Module Def", {"app_name": "cos"}):
            return
    except:
        # 如果数据库连接不可用，仍然尝试加载（可能在安装过程中）
        pass

    folder = frappe.get_app_path("cos", "monkey_patches")
    if not os.path.exists(folder):
        _patches_loaded = True
        return

    # 加载所有补丁文件
    for module_name in os.listdir(folder):
        if not module_name.endswith(".py") or module_name == "__init__.py":
            continue

        try:
            importlib.import_module(f"cos.monkey_patches.{module_name[:-3]}")
            # 不记录成功日志，避免日志噪音
        except Exception as e:
            # 只记录错误日志
            frappe.log_error(
                f"Failed to load monkey patch {module_name}: {str(e)}",
                "Monkey Patch Load Error"
            )

    _patches_loaded = True


# 在模块导入时尝试加载（如果可能）
try:
    if frappe.db:
        _load_monkey_patches_once()
except:
    pass

# 设置 frappe.connect 钩子，确保在连接时加载（如果尚未加载）
# 只在尚未加载且 frappe.connect 存在时设置钩子
if hasattr(frappe, 'connect'):
    # 检查是否已经设置了自定义钩子
    if not hasattr(frappe.connect, '_cos_patch_hook_set'):
        _original_connect = frappe.connect

        def _custom_connect(*args, **kwargs):
            """自定义 connect 函数，在第一次连接时加载 monkey patches（只加载一次）"""
            result = _original_connect(*args, **kwargs)
            _load_monkey_patches_once()
            return result

        _custom_connect._cos_patch_hook_set = True
        frappe.connect = _custom_connect

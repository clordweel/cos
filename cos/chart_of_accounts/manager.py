import os
import shutil
import frappe

# ERPNext 目标存放路径 (V16)
TARGET_DIR = frappe.get_app_path(
    "erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified"
)

# 自定义 App 源路径 (cos)
SOURCE_DIR = frappe.get_app_path("cos", "chart_of_accounts", "custom")


def copy_custom_charts():
    """安装时调用：如果目标已存在则删除，然后复制最新文件"""
    if not os.path.exists(SOURCE_DIR):
        frappe.log_error(
            f"Source directory {SOURCE_DIR} not found.", "Chart Migration Error"
        )
        return

    # 获取自定义 App 目录下的所有 json 文件
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".json")]

    for file_name in files:
        src = os.path.join(SOURCE_DIR, file_name)
        dst = os.path.join(TARGET_DIR, file_name)

        try:
            # --- 核心修改：安装前判断并删除已存在的目标文件 ---
            if os.path.exists(dst):
                os.remove(dst)
                # 使用 frappe.logger 记录，方便在 bench 终端看到
                print(f"Existing file {file_name} removed from target.")

            # 执行复制
            shutil.copy2(src, dst)
            print(f"Successfully copied {file_name} to {TARGET_DIR}")

        except Exception as e:
            frappe.log_error(
                f"Failed to process {file_name} during install: {str(e)}",
                "Chart Migration Error",
            )


def remove_custom_charts():
    """卸载时调用：清理 ERPNext 目录中的相关文件"""
    if not os.path.exists(SOURCE_DIR):
        return

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".json")]

    for file_name in files:
        dst = os.path.join(TARGET_DIR, file_name)

        if os.path.exists(dst):
            try:
                os.remove(dst)
                print(f"Successfully removed {file_name} from {TARGET_DIR}")
            except Exception as e:
                frappe.log_error(
                    f"Failed to remove {file_name}: {str(e)}", "Chart Removal Error"
                )

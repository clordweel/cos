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

    if not files:
        print("[科目表迁移] 未找到需要复制的 JSON 文件")
        return

    print(f"[科目表迁移] 开始复制自定义科目表文件，共 {len(files)} 个文件...")

    success_count = 0
    failed_count = 0

    for file_name in files:
        src = os.path.join(SOURCE_DIR, file_name)
        dst = os.path.join(TARGET_DIR, file_name)

        try:
            # --- 核心修改：安装前判断并删除已存在的目标文件 ---
            if os.path.exists(dst):
                os.remove(dst)
                print(f"  ✓ 已删除旧文件: {file_name}")

            # 执行复制
            shutil.copy2(src, dst)
            print(f"  ✓ 已复制: {file_name} -> {TARGET_DIR}")
            success_count += 1

        except Exception as e:
            print(f"  ✗ 复制失败: {file_name} - {str(e)}")
            failed_count += 1
            frappe.log_error(
                f"Failed to process {file_name} during install: {str(e)}",
                "Chart Migration Error",
            )

    # 输出总结
    print(
        f"[科目表迁移] 完成！成功: {success_count}, 失败: {failed_count}, 总计: {len(files)}")


def remove_custom_charts():
    """卸载时调用：清理 ERPNext 目录中的相关文件"""
    if not os.path.exists(SOURCE_DIR):
        return

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".json")]

    if not files:
        print("[科目表清理] 未找到需要清理的 JSON 文件")
        return

    print(f"[科目表清理] 开始清理自定义科目表文件，共 {len(files)} 个文件...")

    removed_count = 0
    not_found_count = 0
    failed_count = 0

    for file_name in files:
        dst = os.path.join(TARGET_DIR, file_name)

        if os.path.exists(dst):
            try:
                os.remove(dst)
                print(f"  ✓ 已删除: {file_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败: {file_name} - {str(e)}")
                failed_count += 1
                frappe.log_error(
                    f"Failed to remove {file_name}: {str(e)}", "Chart Removal Error"
                )
        else:
            print(f"  - 文件不存在（已跳过）: {file_name}")
            not_found_count += 1

    # 输出总结
    print(
        f"[科目表清理] 完成！已删除: {removed_count}, 不存在: {not_found_count}, 失败: {failed_count}, 总计: {len(files)}")

import frappe
from frappe import _

# 引用 ERPNext 核心公司模块
import erpnext.setup.doctype.company.company as company_module

# 1. 备份原始函数
original_setup_taxes = company_module.setup_taxes_and_charges

# 导入税费模板控制器
from cos.cos_accounts.controllers.company_tax import create_standard_taxes


def patched_setup_taxes_and_charges(company_name, country):
    """
    强化补丁：适配公司初始化时的税费模板创建
    """
    if country == "China":
        # 记录开始执行
        frappe.logger().info(
            f"--- 补丁：开始为 {company_name} 配置中国税率体系 ---"
        )

        # 调用创建函数
        create_standard_taxes(company_name)

        # 拦截成功
        return

    return original_setup_taxes(company_name, country)




def apply_patch():
    company_module.setup_taxes_and_charges = patched_setup_taxes_and_charges

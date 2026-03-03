# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
出库即确认收入：Sales Invoice 从 Delivery Note 创建时，不记收入/销项税，仅做「应收转正」。
"""

import frappe
from frappe import _
from frappe.utils import cint, flt


def before_sales_invoice_gl_entries(doc, method=None):
    """
    在 SI 生成 GL 前判断：若为 against DN 且启用出库即确认收入，则跳过标准收入/应收/销项税，
    改为生成「借 应收账款 贷 应收账款-出库」。
    通过 override get_gl_entries 或 doc_event 实现。
    本模块通过 override_doctype_class 在 get_gl_entries 中调用。
    """
    pass


def should_use_receivable_transfer_logic(doc) -> bool:
    """SI 是否应走「应收转正」逻辑（不记收入/销项税，只记应收转正）。"""
    if cint(doc.update_stock):
        return False
    has_dn = any(row.get("dn_detail") for row in (doc.get("items") or []))
    if not has_dn:
        return False
    ss = frappe.get_single("Selling Settings")
    return bool(ss.get("enable_revenue_at_delivery"))


def get_receivable_transfer_gl_entries(doc) -> list:
    """生成「借 应收账款 贷 应收账款-出库」GL。"""
    if not should_use_receivable_transfer_logic(doc):
        return []

    gl_entries = []
    precision = frappe.get_precision("GL Entry", "debit_in_account_currency") or 2
    base_grand = flt(doc.base_grand_total, precision)

    abbr = frappe.get_cached_value("Company", doc.company, "abbr")
    receivable_at_delivery = f"112203 - 应收账款-出库 - {abbr}"
    debit_to = doc.debit_to

    if not frappe.db.exists("Account", receivable_at_delivery):
        frappe.throw(_("Account {0} not found.").format(receivable_at_delivery))

    # 借 应收账款
    gl_entries.append(doc.get_gl_dict({
        "account": debit_to,
        "party_type": "Customer",
        "party": doc.customer,
        "debit": base_grand,
        "against": doc.customer,
        "against_voucher": doc.name,
        "against_voucher_type": doc.doctype,
        "cost_center": doc.cost_center,
        "project": doc.project,
    }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))

    # 贷 应收账款-出库
    gl_entries.append(doc.get_gl_dict({
        "account": receivable_at_delivery,
        "party_type": "Customer",
        "party": doc.customer,
        "credit": base_grand,
        "against": doc.customer,
        "against_voucher": doc.name,
        "against_voucher_type": doc.doctype,
        "cost_center": doc.cost_center,
        "project": doc.project,
    }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))

    return gl_entries

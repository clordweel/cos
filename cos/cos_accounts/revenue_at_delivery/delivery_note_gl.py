# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
出库即确认收入：Delivery Note 提交时追加收入、应收账款-出库、销项税 GL。
"""

import frappe
from frappe import _


def on_delivery_note_submit(doc, method=None):
    """DN 提交时，若启用出库即确认收入，追加收入/应收账款-出库/销项税 GL。"""
    if not _should_book_revenue_at_delivery(doc):
        return
    _make_revenue_gl_entries(doc)


def on_delivery_note_cancel(doc, method=None):
    """DN 取消时：扩展 ignore_linked_doctypes，允许取消不被 Payment Ledger 阻塞。"""
    if not _should_book_revenue_at_delivery(doc):
        return
    # 标准 DN on_cancel 已冲销 GL（含我们的收入 GL），但 check_no_back_links_exist 会因
    # Payment Ledger Entry 关联而阻止取消。扩展 ignore_linked_doctypes 以放行。
    existing = list(doc.get("ignore_linked_doctypes") or [])
    if "Payment Ledger Entry" not in existing:
        doc.ignore_linked_doctypes = tuple(existing + ["Payment Ledger Entry"])


def _should_book_revenue_at_delivery(doc) -> bool:
    """是否应在出库时确认收入。"""
    if doc.is_return:
        return False
    if not frappe.db.get_value("Company", doc.company, "enable_perpetual_inventory"):
        return False
    ss = frappe.get_single("Selling Settings")
    return bool(ss.get("enable_revenue_at_delivery"))


def _make_revenue_gl_entries(doc):
    """生成收入、应收账款-出库、销项税 GL 并过账。"""
    import erpnext
    if not erpnext.is_perpetual_inventory_enabled(doc.company):
        return

    gl_entries = _get_revenue_gl_entries(doc)
    if not gl_entries:
        return

    from erpnext.accounts.general_ledger import make_gl_entries
    make_gl_entries(gl_entries, merge_entries=False)


def _get_revenue_gl_entries(doc) -> list:
    """按 DN 的 items、taxes 生成 GL 分录。"""
    gl_entries = []
    precision = frappe.get_precision("GL Entry", "debit_in_account_currency") or 2

    # 成本中心：损益类科目必须指定，DN 可能无 cost_center，用 Company 默认兜底
    cost_center = doc.get("cost_center") or frappe.get_cached_value("Company", doc.company, "cost_center")
    if not cost_center:
        frappe.throw(_(
            "Cost Center is required for revenue GL. "
            "Set cost_center on Delivery Note or default cost_center for Company {0}."
        ).format(doc.company))

    # 应收账款-出库科目：112203 - 应收账款-出库 - {abbr}（1122 子科目，与 112201/112202 同级）
    abbr = frappe.get_cached_value("Company", doc.company, "abbr")
    receivable_at_delivery = f"112203 - 应收账款-出库 - {abbr}"
    if not frappe.db.exists("Account", receivable_at_delivery):
        frappe.throw(_("Account {0} not found. Please create 112203 应收账款-出库 for company {1}.").format(
            receivable_at_delivery, doc.company))

    base_grand_total = flt(doc.base_grand_total, precision)

    # 1) 借 应收账款-出库
    gl_entries.append(doc.get_gl_dict({
        "account": receivable_at_delivery,
        "party_type": "Customer",
        "party": doc.customer,
        "debit": base_grand_total,
        "debit_in_account_currency": base_grand_total,
        "against": doc.customer,
        "against_voucher": doc.name,
        "against_voucher_type": doc.doctype,
        "cost_center": cost_center,
        "project": doc.project,
    }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))

    # 2) 贷 收入 + 贷 销项税（按 items 汇总收入，按 taxes 汇总销项税）
    # 收入：按 item 的 income_account 分组汇总；DN 明细可能无 income_account，用 Company.default_income_account 兜底
    default_income = frappe.get_cached_value("Company", doc.company, "default_income_account")
    income_by_account = {}
    for item in doc.items:
        acc = item.get("income_account") or default_income
        if not acc:
            frappe.throw(_(
                "Income account not set for item {0} (row {1}). "
                "Set default_income_account in Company {2} or income_account on the item."
            ).format(item.get("item_code"), item.get("idx"), doc.company))
        amt = flt(item.get("base_net_amount") or 0, precision)
        if amt:
            income_by_account[acc] = income_by_account.get(acc, 0) + amt

    for acc, amt in income_by_account.items():
        if amt <= 0:
            continue
        gl_entries.append(doc.get_gl_dict({
            "account": acc,
            "against": doc.customer,
            "credit": amt,
            "cost_center": cost_center,
            "project": doc.project,
        }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))

    # 销项税
    for tax in doc.get("taxes") or []:
        amt = flt(tax.get("base_tax_amount_after_discount_amount") or 0, precision)
        if amt <= 0:
            continue
        acc = tax.get("account_head")
        if not acc:
            continue
        gl_entries.append(doc.get_gl_dict({
            "account": acc,
            "against": doc.customer,
            "credit": amt,
            "cost_center": tax.get("cost_center") or cost_center,
        }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=tax))

    # 3) 尾差平衡：若 贷方合计 != base_grand_total，记入 round_off_account
    total_credits = sum(flt(e.get("credit") or 0, precision) for e in gl_entries if e.get("account") != receivable_at_delivery)
    diff = flt(base_grand_total - total_credits, precision)
    if abs(diff) > flt(0.01, precision):
        round_off_account, round_off_cc = _get_round_off_account_and_cost_center(doc.company)
        if diff > 0:
            gl_entries.append(doc.get_gl_dict({
                "account": round_off_account,
                "against": doc.customer,
                "credit": diff,
                "credit_in_account_currency": diff,
                "cost_center": round_off_cc or cost_center,
            }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))
        else:
            gl_entries.append(doc.get_gl_dict({
                "account": round_off_account,
                "against": doc.customer,
                "debit": abs(diff),
                "debit_in_account_currency": abs(diff),
                "cost_center": round_off_cc or cost_center,
            }, doc.get("company_currency") or frappe.get_cached_value("Company", doc.company, "default_currency"), item=doc))

    return gl_entries


def _get_round_off_account_and_cost_center(company: str) -> tuple:
    """获取公司的 round_off_account 与 round_off_cost_center。"""
    try:
        from erpnext.accounts.utils import get_round_off_account_and_cost_center as _get
        return _get(company)
    except ImportError:
        company_doc = frappe.get_cached_value(
            "Company", company, ["round_off_account", "round_off_cost_center"], as_dict=True
        )
        acc = (company_doc or {}).get("round_off_account")
        if not acc:
            frappe.throw(_("Company {0} has no round_off_account. Please set it in Company master.").format(company))
        return acc, (company_doc or {}).get("round_off_cost_center")


def flt(val, precision=None):
    return frappe.utils.flt(val, precision)

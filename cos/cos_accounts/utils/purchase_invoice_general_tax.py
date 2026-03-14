# Copyright (c) 2026, bit and contributors
# License: MIT. See LICENSE

"""
采购发票普票/专票处理（方案 A：发票层面区分）

- 专票：税额记进项税额，可抵扣
- 普票：税额记入成本/费用科目（不可抵扣），使用公司配置的 custom_non_deductible_tax_account
"""

from __future__ import annotations

import frappe
from frappe import _


INVOICE_TYPE_SPECIAL = "专票"
INVOICE_TYPE_GENERAL = "普票"


def on_purchase_invoice_validate_general_tax(doc, method=None):
    """
    采购发票 validate：若为普票，将 taxes 表中税额科目的 account_head
    替换为公司的 custom_non_deductible_tax_account（普票税额计入科目）。
    """
    if doc.get("custom_invoice_type") != INVOICE_TYPE_GENERAL:
        return

    company = doc.company
    if not company:
        return

    non_deductible_account = frappe.get_cached_value(
        "Company", company, "custom_non_deductible_tax_account"
    )
    if not non_deductible_account:
        frappe.throw(
            _("普票时需在公司中配置「普票税额计入科目」(custom_non_deductible_tax_account)"),
            title=_("普票配置缺失"),
        )

    # 普票时：所有税额行均记入不可抵扣科目（不进进项税额）
    for row in doc.get("taxes") or []:
        if row.get("account_head"):
            row.account_head = non_deductible_account

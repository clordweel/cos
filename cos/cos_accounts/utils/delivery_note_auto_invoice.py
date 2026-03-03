# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
提交销售出库后自动创建销售发票（系统内开票）。

当 Selling Settings 勾选「出库即确认收入」时，DN 提交后自动从 DN 创建 SI（update_stock=0）并提交，
实现出库当天确认收入。
"""

import frappe
from frappe import _
from frappe.utils import cint


def on_delivery_note_submit(doc, method=None):
    """DN 提交时，若启用自动创建发票，则创建并提交 SI。"""
    if not _should_auto_create_invoice(doc):
        return
    _create_and_submit_sales_invoice(doc)


def _should_auto_create_invoice(doc) -> bool:
    """是否应在 DN 提交后自动创建 SI。"""
    if cint(doc.is_return):
        return False
    ss = frappe.get_single("Selling Settings")
    return bool(ss.get("enable_revenue_at_delivery"))


def _create_and_submit_sales_invoice(doc):
    """从 DN 创建 SI（update_stock=0）并提交。"""
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

    try:
        si_doc = make_sales_invoice(doc.name)
    except Exception as e:
        frappe.log_error(
            title=_("自动创建销售发票失败"),
            message=frappe.get_traceback(),
        )
        frappe.msgprint(
            _("自动创建销售发票失败：{0}").format(str(e)),
            indicator="red",
            alert=True,
        )
        return

    if not si_doc or not si_doc.get("items"):
        return

    si_doc.update_stock = 0
    si_doc.insert()
    si_doc.submit()

    frappe.msgprint(
        _("已自动创建并提交销售发票 {0}").format(si_doc.name),
        indicator="green",
        alert=True,
    )

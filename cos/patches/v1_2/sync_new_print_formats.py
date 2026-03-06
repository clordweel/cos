"""部署时同步发货单、销售发票、采购收货单打印格式模板。"""
from __future__ import annotations

import frappe


def execute():
    from cos.scripts.sync_delivery_note_print_format import sync as sync_dn
    from cos.scripts.sync_sales_invoice_print_format import sync as sync_si
    from cos.scripts.sync_purchase_receipt_print_format import sync as sync_pr

    for sync_fn in (sync_dn, sync_si, sync_pr):
        try:
            sync_fn()
        except FileNotFoundError:
            pass  # 模板文件不存在时跳过（如旧版本）

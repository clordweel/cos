"""部署时同步发货单、销售发票、采购收货单、物料需求外部版等打印格式模板。"""
from __future__ import annotations

import frappe


def execute():
    from cos.scripts.sync_delivery_note_print_format import sync as sync_dn
    from cos.scripts.sync_sales_invoice_print_format import sync as sync_si
    from cos.scripts.sync_purchase_receipt_print_format import sync as sync_pr
    from cos.scripts.sync_material_request_external import sync as sync_mr_external

    for sync_fn in (sync_dn, sync_si, sync_pr, sync_mr_external):
        try:
            sync_fn()
        except FileNotFoundError as e:
            frappe.log_error(
                title=f"Print Format sync skipped: {sync_fn.__module__}",
                message=str(e),
            )

# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
Sales Invoice 扩展：当从 DN 创建且启用出库即确认收入时，仅做应收转正，不记收入/销项税。
"""

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from .sales_invoice_gl import get_receivable_transfer_gl_entries, should_use_receivable_transfer_logic


class SalesInvoiceRevenueAtDelivery(SalesInvoice):
    def get_gl_entries(self, inventory_account_map=None):
        if should_use_receivable_transfer_logic(self):
            # 仅应收转正，不记收入/应收/销项税（此时 update_stock=0）
            gl_entries = get_receivable_transfer_gl_entries(self)
            from erpnext.accounts.general_ledger import merge_similar_entries
            gl_entries = merge_similar_entries(gl_entries)
            self.make_loyalty_point_redemption_gle(gl_entries)
            self.make_pos_gl_entries(gl_entries)
            self.make_write_off_gl_entry(gl_entries)
            self.make_gle_for_rounding_adjustment(gl_entries)
            self.set_transaction_currency_and_rate_in_gl_map(gl_entries)
            return gl_entries
        return super().get_gl_entries(inventory_account_map)

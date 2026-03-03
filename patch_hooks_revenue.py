#!/usr/bin/env python3
"""Patch cos hooks.py for revenue_at_delivery."""
from pathlib import Path
# 脚本放在 cos 应用根目录时，hooks 在 cos/hooks.py
base = Path(__file__).resolve().parent
path = base / "cos" / "hooks.py"
if not path.exists():
    path = base / "hooks.py"  # 或 hooks 在应用根
path = str(path)
content = open(path, encoding="utf-8").read()

if "revenue_at_delivery" in content:
    print("Already patched")
    exit(0)

# Add Delivery Note to doc_events
if '"Delivery Note"' not in content:
    content = content.replace(
        '"Sales Invoice": {',
        '"Delivery Note": {\n        "on_submit": "cos.cos_accounts.revenue_at_delivery.delivery_note_gl.on_delivery_note_submit",\n    },\n    "Sales Invoice": {',
    )
    print("Added Delivery Note")

# Add override_doctype_class
if "SalesInvoiceRevenueAtDelivery" not in content:
    old = "# Overriding Methods"
    new = """# 出库即确认收入
override_doctype_class = {
    "Sales Invoice": "cos.cos_accounts.revenue_at_delivery.sales_invoice_override.SalesInvoiceRevenueAtDelivery",
}

# Overriding Methods"""
    content = content.replace(old, new, 1)
    print("Added override_doctype_class")

open(path, "w", encoding="utf-8").write(content)
print("Patched successfully")

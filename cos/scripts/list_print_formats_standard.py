# Copyright (c) 2026, COS and contributors
"""列出名称包含「标准」的 Print Format，用于验证部署。

用法（在 dev 服务器上）:
  bench --site junhai.local execute cos.scripts.list_print_formats_standard.list_standard
"""

from __future__ import annotations

import frappe


def list_standard(site: str | None = None) -> list[dict]:
    frappe.connect(site=site)
    rows = frappe.get_all(
        "Print Format",
        filters={"name": ["like", "%标准%"]},
        fields=["name", "doc_type"],
        order_by="name",
    )
    return rows

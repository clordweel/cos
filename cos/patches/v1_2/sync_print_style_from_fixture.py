"""从 fixture 同步 Print Style，确保部署后样式（含页码底部边距）生效。"""
from __future__ import annotations

import json
from pathlib import Path

import frappe


def execute():
    app_path = Path(frappe.get_app_path("cos"))
    fixture_path = app_path / "fixtures" / "print_style.json"
    if not fixture_path.exists():
        return
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    for record in data:
        name = record.get("name") or record.get("print_style_name")
        if not name or name != "COS 通用打印样式":
            continue
        if not frappe.db.exists("Print Style", name):
            continue
        doc = frappe.get_doc("Print Style", name)
        if record.get("css") is not None and doc.css != record["css"]:
            doc.css = record["css"]
            doc.flags.ignore_permissions = True
            doc.save()
        break

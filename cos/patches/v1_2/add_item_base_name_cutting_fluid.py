"""新增物料基础名「切削液」，用于金属加工冷却润滑。幂等。"""
from __future__ import annotations

import frappe

BASE_NAME = "切削液"
ABBREVIATION = "QXY"
DESCRIPTION = "切削液物料基础名，用于金属加工冷却润滑。"


def execute():
    if not frappe.db.exists("DocType", "Item Base Name"):
        return
    if frappe.db.exists("Item Base Name", BASE_NAME):
        return
    doc = frappe.new_doc("Item Base Name")
    doc.base_name = BASE_NAME
    doc.abbreviation = ABBREVIATION
    doc.description = DESCRIPTION
    doc.flags.ignore_permissions = True
    doc.insert()

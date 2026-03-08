# -*- coding: utf-8 -*-
"""为 Item 回填 custom_item_base_name；缺失时可选创建 Item Base Name。供 bench execute 在服务器上执行。

用法（在 bench 所在机器）：
  bench --site junhai.local execute cos.backfill_item_base_name.run_backfill --kwargs '{"allow_create_missing": true}'
  bench --site junhai.local execute cos.backfill_item_base_name.run_backfill --kwargs '{"allow_create_missing": true, "dry_run": true}'
"""
from __future__ import annotations

import frappe


def _norm(s):
    return (s or "").strip()[:200]


def run_backfill(allow_create_missing=False, dry_run=False):
    """回填 Item.custom_item_base_name；不修改物料编码。返回 stats 字典。"""
    if not frappe.db.exists("DocType", "Item Base Name"):
        return {"error": "Item Base Name DocType 不存在", "stats": {}}

    all_items = frappe.get_all(
        "Item",
        filters={},
        fields=["name", "item_name", "description", "custom_item_base_name"],
    )
    items = [it for it in all_items if not (it.get("custom_item_base_name") or "").strip()]
    if not items:
        return {
            "ok": True,
            "message": "无待回填 Item",
            "stats": {"linked": 0, "created_base_name": 0, "skipped": 0, "failed": 0},
        }

    base_names = frappe.get_all(
        "Item Base Name",
        filters={},
        fields=["name", "base_name"],
    )
    base_name_by_name = {r["name"]: r["base_name"] for r in base_names}
    norm_to_bn_name = {}
    for r in base_names:
        k = _norm(r.get("base_name"))
        if k:
            norm_to_bn_name.setdefault(k, r["name"])

    # 已有缩写集合（用于新建时唯一）
    try:
        abbr_list = frappe.get_all(
            "Item Base Name",
            filters=[["abbreviation", "!=", ""]],
            pluck="abbreviation",
        )
    except Exception:
        abbr_list = []
    created_abbr_used = set(abbr_list) if abbr_list else set()

    linked = 0
    created_base_name = 0
    skipped = 0
    failed = []

    for it in items:
        iname = _norm(it.get("item_name"))
        desc = _norm(it.get("description"))
        cand = iname or desc or ""
        if not cand:
            skipped += 1
            continue
        bn_name = None
        if cand in norm_to_bn_name:
            bn_name = norm_to_bn_name[cand]
        else:
            for bn, bname in base_name_by_name.items():
                bnorm = _norm(bn)
                if not bnorm:
                    continue
                if bnorm == cand or cand.startswith(bnorm) or bnorm.startswith(cand):
                    bn_name = bname
                    break
        if bn_name:
            if not dry_run:
                frappe.db.set_value("Item", it["name"], "custom_item_base_name", bn_name)
            linked += 1
            continue
        if not allow_create_missing:
            skipped += 1
            continue
        base_name = (iname or desc or it["name"])[:80].strip()
        if not base_name:
            skipped += 1
            continue
        if base_name in norm_to_bn_name:
            bn_name = norm_to_bn_name[base_name]
            if not dry_run:
                frappe.db.set_value("Item", it["name"], "custom_item_base_name", bn_name)
            linked += 1
            continue
        orig_base = base_name
        suffix = 1
        while base_name in norm_to_bn_name or frappe.db.exists("Item Base Name", base_name):
            base_name = orig_base + "_" + str(suffix)
            suffix += 1
        abbr = "ITM"
        for c in base_name:
            if c.isalnum():
                abbr = (abbr + c.upper())[:6]
                break
        if len(abbr) < 3:
            abbr = (base_name[:3] or "ITM").upper()
        abbr = "".join(c for c in abbr if c.isalnum())[:20] or "ITM"
        while abbr in created_abbr_used:
            abbr = abbr[:16] + str(suffix)
            suffix += 1
        created_abbr_used.add(abbr)
        if not dry_run:
            doc = frappe.new_doc("Item Base Name")
            doc.base_name = base_name
            doc.abbreviation = abbr
            doc.insert()
            frappe.db.set_value("Item", it["name"], "custom_item_base_name", doc.name)
            norm_to_bn_name[base_name] = doc.name
            base_name_by_name[doc.name] = base_name
        created_base_name += 1
        linked += 1

    if not dry_run and (linked or created_base_name):
        frappe.db.commit()

    stats = {"linked": linked, "created_base_name": created_base_name, "skipped": skipped, "failed": len(failed)}
    if failed:
        stats["failed_items"] = failed[:20]
    return {"ok": True, "stats": stats}

# -*- coding: utf-8 -*-
"""为 Item 回填 custom_item_base_name；缺失时可选创建 Item Base Name。供 bench execute 在服务器上执行。

基础名具有语义（类别/类型，如 螺栓、螺母），创建缺失时不应盲目复制整条物料名称，而应从名称中
派生简短候选（如首词、规格前的部分），仅当候选合理且较短时才创建。
"""
from __future__ import annotations

import re
import frappe


def _norm(s):
    return (s or "").strip()[:200]


def _derive_base_name_candidate(item_name: str, description: str) -> str | None:
    """从物料名称/描述派生候选基础名（类别级，非完整规格）。不宜过长，不含规格数字等。"""
    raw = _norm(item_name) or _norm(description)
    if not raw:
        return None
    # 规格常见模式：空格/逗号/×/x 后跟数字或尺寸，取之前部分作为类别
    for sep in [" ", "\t", "，", ",", "×", "x", "X"]:
        if sep in raw:
            head = raw.split(sep)[0].strip()
            if head and len(head) <= 8:
                return head
    # 若含数字，取第一个连续非数字片段（如 "M8x30" 取 "M" 太短；"衬板128" 取 "衬板"）
    m = re.match(r"^([\u4e00-\u9fffA-Za-z]+)", raw)
    if m:
        head = m.group(1).strip()
        if 2 <= len(head) <= 8:
            return head
    # 仅取前若干字作为候选（基础名通常 2～6 字）
    head = raw[:6].strip()
    if len(head) >= 2 and not head.isdigit():
        return head
    return None


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
        # 基础名有语义，不盲目复制整条物料名称；仅用派生的简短候选
        base_name = _derive_base_name_candidate(it.get("item_name") or "", it.get("description") or "")
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

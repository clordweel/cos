"""为已有 Item Base Name 填充缩写字段（用于物料编码前缀）。

缩写优先级（保证唯一性）：
  1. 英文短词：如 Bolt->BLT, Nut->NT, O型圈->OR
  2. 单词过长或词组：英文首字母缩写，如 Deep Groove Ball Bearing->DGBB
  3. 最后才用拼音缩写：如 方管->FG（无通用英文时）

若与库中已有或其他映射冲突，自动追加数字后缀（如 BLT2）确保唯一。
仅更新当前缩写为空的记录。
"""
from __future__ import annotations

import frappe

# 基础名 -> 首选缩写（优先英文短词/首字母，其次拼音；execute 内会做唯一性解析）
BASE_NAME_ABBREVIATION = {
    # --- 英文短词 ---
    "螺栓": "BLT",  # Bolt
    "螺母": "NT",  # Nut
    "电机": "MTR",  # Motor
    "轴承": "BRG",  # Bearing
    "电缆": "CBL",  # Cable
    "电线": "WIR",  # Wire
    "垫圈": "WSH",  # Washer
    "球阀": "BV",  # Ball valve
    "O型圈": "OR",  # O-Ring
    "减速机": "RDR",  # Reducer
    "联轴器": "CPL",  # Coupling
    "密封垫": "GKT",  # Gasket
    "液压油": "HYO",  # Hydraulic oil
    "齿轮油": "GEO",  # Gear oil
    "润滑脂": "GRS",  # Grease
    "断路器": "CBR",  # Circuit breaker
    "钢板": "SPL",  # Steel plate
    "衬板": "LNR",  # Liner
    "管材": "PPE",  # Pipe
    "型材": "SCT",  # Section
    "棒材": "BAR",  # Bar
    "板材": "PLT",  # Plate
    "圆钢": "RDB",  # Round bar
    "角钢": "ANG",  # Angle
    "槽钢": "CHN",  # Channel
    "扁钢": "FLT",  # Flat
    "工字钢": "IBM",  # I-beam
    "H 型钢": "HBM",  # H-beam
    "紧固件": "FST",  # Fastener
    "原材料": "RWM",  # Raw material
    "密封件": "SEL",  # Seal
    "液压件": "HYD",  # Hydraulic
    "刀具": "TOL",  # Tool
    "胶": "ADH",  # Adhesive
    "球磨机": "BLM",  # Ball mill
    "烘干机": "DRY",  # Dryer
    "筛分机": "SCR",  # Screen
    "服务": "SVC",  # Service
    "委外加工": "SBC",  # Subcontract
    "传动轴": "DRS",  # Drive shaft
    "小齿轮": "PIN",  # Pinion
    "大齿轮": "GR",  # Gear
    "托辊": "IDL",  # Idler
    "输送带": "CVB",  # Conveyor belt
    "控制柜": "CTC",  # Control cabinet
    "柜体": "CAB",  # Cabinet
    "签字笔": "PEN",  # Pen
    "行政办公": "OFC",  # Office
    "底漆": "PRM",  # Primer
    "面漆": "TPC",  # Top coat
    "固化剂": "HRD",  # Hardener
    "稀释剂": "THN",  # Thinner
    "耐火材料": "REF",  # Refractory
    "动力设备": "PWE",  # Power equipment
    "化工辅料": "CHA",  # Chemical auxiliary
    "润滑油脂": "LUB",  # Lubricant
    "抗磨液压油": "AWHO",  # Anti-wear hydraulic oil
    "方管": "SQT",  # Square tube
    "圆管": "RDT",  # Round tube
    "深沟球轴承": "DGBB",  # Deep groove ball bearing
    "无缝钢管": "SSP",  # Seamless steel pipe
    "系列成品": "SCP",  # Series product
    # --- 英文首字母 / 拼音混合（无通用短词时）---
    "直缝焊管": "ZFHG",
    "不锈钢管": "BXG",
    "带座轴承": "DZZC",
    "小齿轮轴": "XCLZ",
    "托轮轴": "TLZ",
    "微型断路器": "WXDLQ",
    "硬齿面减速机": "YCMJ",
    "行星减速机": "XXJS",
    "摆线针轮": "BXZL",
    "三相异步电动机": "SXYB",
    "内六角圆柱头螺钉": "NLJY",
    "沉头螺钉": "CTLD",
    "紧定螺钉": "JDLD",
    "六角头螺栓": "LJTL",
    "六角螺母": "LJLM",
    "法兰面螺母": "FLM",
    "I型六角螺母": "IXLM",
    "平垫圈": "PDQ",
    "弹簧垫圈": "THDQ",
    "轴用挡圈": "ZYDQ",
    "筒体衬板": "TTCB",
    "端盖衬板": "DGCB",
    "磨头衬板": "MTCB",
    "隔仓篦板": "GCB",
    "研磨介质": "YMJZ",
    "钢球": "GQ",
    "钢段": "GD",
    "陶瓷球": "TCQ",
    "耐火砖": "NHZ",
    "浇注料": "JZL",
    "耐火泥": "NHN",
    "保温棉": "BWM",
    "传动件": "CDJ",
    "普通V带": "PTVD",
    "调心滚子轴承": "TXGZ",
    "推力球轴承": "TLQZ",
    "圆锥滚子轴承": "YZGZ",
    "紧定套": "JDT",
    "弹性柱销联轴器": "TXZX",
    "梅花联轴器": "MHLZ",
    "轴类": "ZL",
    "销轴": "XZ",
    "传动滚筒": "CDGT",
    "改向滚筒": "GXGT",
    "增面滚筒": "ZMGT",
    "羊毛毡圈": "YMZQ",
    "密封条": "MFT",
    "盘根": "PG",
    "石墨密封块": "SMMF",
    "非标垫片": "FBDP",
    "回转部分": "HZBF",
    "耗材": "HC",
    "电焊条": "DHT",
    "实心焊丝": "SXHS",
    "药芯焊丝": "YXHS",
    "埋弧焊丝": "MHHS",
    "焊剂": "HJ",
    "电气件": "DQJ",
    "高压胶管总成": "GYJG",
    "数控刀片": "SKDP",
    "油漆涂料": "YQTL",
    "螺纹胶": "LWJ",
    "密封胶": "MFJA",
}


def _resolve_unique_abbreviations(
    rows_to_update: list[dict],
    existing_abbreviations: set[str],
) -> dict[str, str]:
    """为待更新的 (docname -> 首选缩写) 解析出最终唯一缩写；冲突时追加数字后缀。"""
    docname_to_abbr = {}
    used = set(existing_abbreviations)
    for row in sorted(rows_to_update, key=lambda r: (r.get("base_name") or "", r["name"])):
        docname = row["name"]
        preferred = BASE_NAME_ABBREVIATION.get(row.get("base_name") or "")
        if not preferred:
            continue
        final = preferred
        suffix = 1
        while final in used:
            suffix += 1
            final = f"{preferred}{suffix}"
        used.add(final)
        docname_to_abbr[docname] = final
    return docname_to_abbr


def execute():
    if not frappe.db.exists("DocType", "Item Base Name"):
        return
    try:
        if not frappe.db.has_column("tabItem Base Name", "abbreviation"):
            return
    except Exception:
        return
    rows = frappe.get_all(
        "Item Base Name",
        filters={},
        fields=["name", "base_name", "abbreviation"],
    )
    existing_abbreviations = {r["abbreviation"] for r in rows if r.get("abbreviation")}
    rows_to_update = [
        r for r in rows
        if (r.get("base_name") and not r.get("abbreviation") and r["base_name"] in BASE_NAME_ABBREVIATION)
    ]
    if not rows_to_update:
        return
    docname_to_abbr = _resolve_unique_abbreviations(rows_to_update, existing_abbreviations)
    for docname, abbr in docname_to_abbr.items():
        frappe.db.set_value(
            "Item Base Name",
            docname,
            "abbreviation",
            abbr,
            update_modified=False,
        )
    frappe.db.commit()

# Copyright (c) 2025, cos and contributors
# License: GNU General Public License v3. See license.txt
"""
资产负债表（中国准则）- 基于 ERPNext Balance Sheet，适配中国企业会计准则格式。
账户式结构：左资产（流动资产、非流动资产），右负债（流动负债、非流动负债）+ 所有者权益。
"""

import frappe
from frappe import _

from erpnext.accounts.report.balance_sheet.balance_sheet import execute as balance_sheet_execute


def execute(filters=None):
    """复用标准 Balance Sheet 逻辑，输出中国准则格式。"""
    if not filters:
        filters = frappe._dict()

    result = balance_sheet_execute(filters)
    columns = result[0]
    data = result[1]
    message = result[2]
    chart = result[3] if len(result) > 3 else None
    report_summary = result[4] if len(result) > 4 else None
    primitive_summary = result[5] if len(result) > 5 else None

    # 按中国准则重新排序：流动资产 -> 非流动资产 -> 流动负债 -> 非流动负债 -> 所有者权益
    if data:
        data = _reorder_for_china_format(data, filters)

    if report_summary is not None and primitive_summary is not None:
        return columns, data, message, chart, report_summary, primitive_summary
    if chart is not None:
        return columns, data, message, chart
    return columns, data, message


def _reorder_for_china_format(data, filters):
    """
    将 Balance Sheet 数据按中国准则顺序重排。
    标准输出为 Asset | Liability | Equity，需按 account_number 拆分为：
    资产：流动资产(1xxx 部分) -> 非流动资产(15xx-19xx)
    负债：流动负债(2xxx 部分) -> 非流动负债(25xx, 27xx...)
    权益：实收资本、资本公积、盈余公积、未分配利润
    """
    # 中国准则科目编码范围（一级）
    CURRENT_ASSET_PREFIXES = ("1001", "1002", "1012", "1101", "1111", "1121", "1122", "1123", "1131", "1132", "1221", "1231", "1401", "1402", "1403", "1404", "1405", "1406", "1407", "1408", "1409", "1410", "1411")
    NONCURRENT_ASSET_PREFIXES = ("1501", "1511", "1521", "1531", "1532", "1541", "1601", "1602", "1603", "1604", "1605", "1606", "1611", "1701", "1702", "1703", "1711", "1801", "1811", "1901")
    CURRENT_LIABILITY_PREFIXES = ("2001", "2101", "2201", "2202", "2203", "2211", "2221", "2231", "2232", "2241", "2245", "2251", "2261", "2311", "2312", "2313", "2314")
    NONCURRENT_LIABILITY_PREFIXES = ("2501", "2502", "2601", "2602", "2701", "2711", "2801", "2811", "2901")
    EQUITY_PREFIXES = ("4001", "4002", "4101", "4102", "4103", "4104", "4201")

    def _get_account_num(row):
        acc = row.get("account") or ""
        if isinstance(acc, str) and " - " in acc:
            return acc.split(" - ")[0].strip()
        num = row.get("account_number")
        return str(num).strip() if num is not None else ""

    def _match_prefix(num, prefixes):
        if not num:
            return False
        for p in prefixes:
            if num == p or num.startswith(p + "-") or num.startswith(p + " "):
                return True
        # 子科目：112101 属于 1121
        for p in prefixes:
            if num.startswith(p):
                return True
        return False

    assets_current = []
    assets_noncurrent = []
    liabilities_current = []
    liabilities_noncurrent = []
    equity_rows = []
    other = []  # 汇总行、未分配利润等

    i = 0
    in_equity = False
    seen_equity_section = False

    while i < len(data):
        row = data[i]
        if not isinstance(row, dict):
            i += 1
            continue

        acc_name = (row.get("account_name") or row.get("account") or "")
        acc_str = str(acc_name)
        num = _get_account_num(row)

        # 识别汇总行、临时行（无 account 的合计行）
        if "'" in acc_str or "Total" in acc_str or "Provisional" in acc_str or "Unclosed" in acc_str:
            other.append(row)
            i += 1
            continue

        # 根据 account 或 account_number 判断类型
        if _match_prefix(num, EQUITY_PREFIXES) or "实收资本" in acc_str or "资本公积" in acc_str or "盈余公积" in acc_str or "未分配利润" in acc_str or "所有者权益" in acc_str:
            equity_rows.append(row)
            seen_equity_section = True
        elif _match_prefix(num, CURRENT_ASSET_PREFIXES):
            assets_current.append(row)
        elif _match_prefix(num, NONCURRENT_ASSET_PREFIXES):
            assets_noncurrent.append(row)
        elif _match_prefix(num, CURRENT_LIABILITY_PREFIXES):
            liabilities_current.append(row)
        elif _match_prefix(num, NONCURRENT_LIABILITY_PREFIXES):
            liabilities_noncurrent.append(row)
        elif seen_equity_section and ("Asset" in str(row.get("root_type", "")) or not row.get("root_type")):
            # 可能是资产类但未匹配到
            assets_noncurrent.append(row)
        elif seen_equity_section and ("Liability" in str(row.get("root_type", "")) or not row.get("root_type")):
            liabilities_noncurrent.append(row)
        else:
            # 默认按 root_type 或顺序
            if row.get("root_type") == "Asset":
                assets_noncurrent.append(row)
            elif row.get("root_type") == "Liability":
                liabilities_noncurrent.append(row)
            elif row.get("root_type") == "Equity":
                equity_rows.append(row)
            else:
                other.append(row)
        i += 1

    # 若未成功分类，则保持原序
    if not assets_current and not assets_noncurrent and not liabilities_current and not liabilities_noncurrent and not equity_rows:
        return data

    result = []
    result.extend(assets_current)
    result.extend(assets_noncurrent)
    result.extend(liabilities_current)
    result.extend(liabilities_noncurrent)
    result.extend(equity_rows)
    result.extend(other)

    return result

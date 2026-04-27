# Copyright (c) 2026, COS and contributors
"""财务相关打印模板 Jinja 全局方法。"""

from __future__ import annotations

import json

import frappe
from frappe.utils import flt

from cos.cos_accounts.utils.currency import get_rmb_upper


def rmb_upper_amount(amount):
	"""金额中文大写（人民币），供打印格式 Jinja 使用。"""
	return get_rmb_upper(amount)


def payment_request_ref_item_pricing(ref_doc, item):
	"""关联订单/发票行：含税单价、含税金额、税率%（税额按表头税费与行净额占比分摊）。

	根因说明（+0.01 类问题）：表头 `taxes` 里常有余额舍入的极小 tax_amount；行上若
	`net_amount` 与 `amount` 已相等（或仅用 amount 表示行小计），行金额已是价税结果，
	再按「行 net / 整单 net」把表头税摊到行，会把 0.01 税**重复加**到行上，出现
	560+0.01。对此：行 net≈amount 时直接取行 `amount`；并保留与行/整单合计的 0.01 对齐。"""  # noqa: E501
	if not ref_doc or not item:
		return frappe._dict(rate_pct=None, gross_rate=0.0, gross_amount=0.0)

	items = ref_doc.get("items") or []
	n_items = len(items)
	qty = flt(item.get("qty") or 0)

	n_amt = flt(item.get("net_amount") or 0)
	a_amt = flt(item.get("amount") or 0)

	# 行上已「净=额」或二者均视为行价税小计，不再从 taxes 子表加摊
	if n_amt and a_amt and abs(n_amt - a_amt) < 0.01:
		gross_amt = flt(a_amt, 2)
		gross_rate = flt(flt(gross_amt) / flt(qty), 2) if qty else 0.0
	else:
		net = n_amt if n_amt else a_amt

		total_net = flt(getattr(ref_doc, "net_total", None) or 0)
		if not total_net:
			total_net = sum(
				flt(r.get("net_amount") or r.get("amount") or 0) for r in items
			)

		total_tax = 0.0
		for t in ref_doc.get("taxes") or []:
			ta = flt(t.get("tax_amount") or 0)
			if ta > 0:
				total_tax += ta

		line_tax = 0.0
		if total_net > 0 and total_tax > 0 and net > 0:
			line_tax = flt(
				flt(total_tax) * (flt(net) / flt(total_net)),
				2,
			)

		gross_amt = flt(flt(net) + flt(line_tax, 2), 2)
		gross_rate = flt(flt(gross_amt) / flt(qty), 2) if qty else 0.0

		# 与行「金额」、整单 total 做 0.01 内对齐
		if a_amt and abs(flt(gross_amt) - a_amt) <= 0.01:
			gross_amt = flt(a_amt, 2)
			gross_rate = flt(flt(gross_amt) / flt(qty), 2) if qty else 0.0
		if n_items == 1 and getattr(ref_doc, "grand_total", None) is not None:
			gtot = flt(getattr(ref_doc, "grand_total", 0) or 0)
			if gtot and abs(flt(gross_amt) - gtot) <= 0.01:
				gross_amt = flt(gtot, 2)
				gross_rate = flt(flt(gross_amt) / flt(qty), 2) if qty else 0.0

	rate_pct = None
	tr = item.get("item_tax_rate")
	if tr:
		if isinstance(tr, str) and tr.strip().startswith("{"):
			try:
				tr = json.loads(tr)
			except (TypeError, ValueError):
				tr = {}
		if isinstance(tr, dict) and tr:
			rate_pct = sum(flt(v) for v in tr.values())
	if rate_pct is None or flt(rate_pct) == 0:
		for t in ref_doc.get("taxes") or []:
			r = flt(t.get("rate") or 0)
			if r and flt(t.get("tax_amount") or 0) != 0:
				rate_pct = r
				break
	if rate_pct is None or flt(rate_pct) == 0:
		for t in ref_doc.get("taxes") or []:
			r = flt(t.get("rate") or 0)
			if r:
				rate_pct = r
				break

	return frappe._dict(
		rate_pct=flt(rate_pct) if rate_pct is not None else None,
		gross_rate=gross_rate,
		gross_amount=gross_amt,
	)

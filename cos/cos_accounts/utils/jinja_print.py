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
	"""关联订单/发票行：含税单价、含税金额、税率%（税额按表头税费总额与行 net 占比分摊）。"""
	if not ref_doc or not item:
		return frappe._dict(rate_pct=None, gross_rate=0.0, gross_amount=0.0)

	items = ref_doc.get("items") or []
	qty = flt(item.get("qty") or 0)

	net = flt(item.get("net_amount"))
	if not net:
		net = flt(item.get("amount") or 0)

	total_net = flt(getattr(ref_doc, "net_total", None) or 0)
	if not total_net:
		total_net = sum(flt(r.get("net_amount") or r.get("amount") or 0) for r in items)

	total_tax = 0.0
	for t in ref_doc.get("taxes") or []:
		ta = flt(t.get("tax_amount") or 0)
		if ta > 0:
			total_tax += ta

	line_tax = 0.0
	if total_net > 0 and total_tax > 0 and net > 0:
		line_tax = total_tax * (net / total_net)

	gross_amt = net + line_tax
	gross_rate = (gross_amt / qty) if qty else 0.0

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

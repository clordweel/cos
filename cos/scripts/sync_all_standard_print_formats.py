# Copyright (c) 2026, COS and contributors
"""在服务器上一键同步所有标准打印格式（从 print_format/* 模板到 Print Format 文档）。

用法:
  bench --site junhai.local execute cos.scripts.sync_all_standard_print_formats.sync_all
"""

from __future__ import annotations


def sync_all(site: str | None = None) -> list[dict]:
	"""按顺序执行各标准打印格式的 sync，返回每项结果列表。"""
	modules = [
		("cos.scripts.sync_stock_reconciliation_print_format", "sync"),
		("cos.scripts.sync_delivery_note_print_format", "sync"),
		("cos.scripts.sync_sales_invoice_print_format", "sync"),
		("cos.scripts.sync_purchase_receipt_print_format", "sync"),
		("cos.scripts.sync_purchase_order_print_format", "sync"),
		("cos.scripts.sync_stock_entry_print_format", "sync"),
		("cos.scripts.sync_sale_order_print_format", "sync"),
		("cos.scripts.sync_pick_list_print_format", "sync"),
		("cos.scripts.sync_material_request_print_format", "sync"),
	]
	results = []
	import frappe
	for mod_name, fn_name in modules:
		try:
			mod = __import__(mod_name, fromlist=[fn_name])
			fn = getattr(mod, fn_name)
			out = fn(site=site)
			results.append({"module": mod_name, "ok": True, "result": out})
		except FileNotFoundError as e:
			results.append({"module": mod_name, "ok": False, "error": str(e)})
		except Exception as e:
			results.append({"module": mod_name, "ok": False, "error": str(e)})
	return results

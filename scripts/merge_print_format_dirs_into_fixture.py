#!/usr/bin/env python3
"""将 print_format/<subdir>/ 中尚未进入 fixture 的模板合并进 cos/fixtures/print_format.json。

仅作一次性/维护用；日常请以 print_format.json 为唯一真相源（见 print_format/README.md）。
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "cos" / "fixtures" / "print_format.json"
PF_DIR = REPO_ROOT / "print_format"


def _now_modified() -> str:
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def main() -> None:
	rows: list[dict] = json.loads(FIXTURE.read_text(encoding="utf-8"))
	by_name = {r["name"]: r for r in rows}

	def clone_from(source_name: str, name: str, doc_type: str, module: str) -> dict:
		src = by_name[source_name]
		r = copy.deepcopy(src)
		r["name"] = name
		r["doc_type"] = doc_type
		r["module"] = module
		r["modified"] = _now_modified()
		return r

	# (fixture name, doc_type, module, subdir, clone_from_name)
	additions: list[tuple[str, str, str, str, str]] = [
		("发货单 - 标准", "Delivery Note", "COS Share", "delivery-note-standard", "销售订单 - 标准"),
		("入库单 - 标准", "Purchase Receipt", "COS Share", "purchase-receipt-standard", "采购订单 - 标准"),
		("销售发票 - 标准", "Sales Invoice", "COS Share", "sales-invoice-standard", "销售订单 - 标准"),
		("物料需求 - 平台询价", "Material Request", "COS Stock", "material-request-b2b-platform", "物料需求 - 标准"),
		(
			"供应商报价单 - 外部 - 无单价",
			"Supplier Quotation",
			"COS Buying",
			"supplier-quotation-external-no-price",
			"报价单 - 标准",
		),
	]

	for name, doc_type, module, subdir, clone_src in additions:
		sub = PF_DIR / subdir
		tpl = sub / "template.html"
		css_f = sub / "styles.css"
		if not tpl.is_file():
			raise SystemExit(f"缺少模板: {tpl}")
		html = tpl.read_text(encoding="utf-8")
		css = css_f.read_text(encoding="utf-8") if css_f.is_file() else ""
		if name in by_name:
			by_name[name]["html"] = html
			by_name[name]["css"] = css
			by_name[name]["modified"] = _now_modified()
		else:
			row = clone_from(clone_src, name, doc_type, module)
			row["html"] = html
			row["css"] = css
			rows.append(row)
			by_name[name] = row

	# 物料移动 - 标准：以 material-movement-standard 目录为准覆盖
	mm_name = "物料移动 - 标准"
	mm_sub = PF_DIR / "material-movement-standard"
	if mm_name not in by_name:
		raise SystemExit(f"fixture 中缺少: {mm_name}")
	tpl_mm = mm_sub / "template.html"
	css_mm = mm_sub / "styles.css"
	if tpl_mm.is_file():
		by_name[mm_name]["html"] = tpl_mm.read_text(encoding="utf-8")
		by_name[mm_name]["css"] = css_mm.read_text(encoding="utf-8") if css_mm.is_file() else ""
		by_name[mm_name]["modified"] = _now_modified()

	FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
	print(f"已写入 {FIXTURE}，共 {len(rows)} 条 Print Format。")


if __name__ == "__main__":
	main()

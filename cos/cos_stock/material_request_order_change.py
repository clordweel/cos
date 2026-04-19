# Copyright (c) 2025, COS and contributors
# License: MIT. See license.txt

"""物料需求单提交后明细变更：Update Items 流程。"""

import json

import frappe
from frappe import _
from frappe.utils import flt

from cos.cos_stock.utils.material_request import can_update_material_request_items


def validate_mr_item_qty_on_update(doc, method=None):
	"""提交后变更时校验：qty 不能小于 ordered_qty。"""
	if doc.get("_action") != "update_after_submit":
		return
	for item in doc.items:
		if flt(item.qty) < flt(item.ordered_qty):
			frappe.throw(
				_("行 #{0}：物料 {1} 的数量不能小于已下单数量 {2}。").format(
					item.idx, item.item_code, item.ordered_qty
				),
				title=_("数量无效"),
			)


def on_mr_update_after_submit(doc, method=None):
	"""提交后变更完成后，更新 indented_qty；Purchase MR 重算 per_ordered 与状态。

	标准逻辑里 Purchase 类型 MR 的 ordered_qty / per_ordered 由采购单 status_updater 写回，
	MaterialRequest.update_completed_qty 对 Purchase 直接 return，不在本单内重算百分比。
	若仅在 MR 上提交后删改明细（删去未下单行、调整 qty 等），父单 per_ordered 会滞留旧值，
	状态会错误保持「部分已下单」。此处与 update_completed_qty 中非 Purchase 分支一致，按子表汇总重算。
	"""
	if doc.get("_action") != "update_after_submit":
		return
	doc.update_requested_qty()
	if doc.material_request_type == "Purchase":
		doc._update_percent_field(
			{
				"target_dt": "Material Request Item",
				"target_parent_dt": doc.doctype,
				"target_parent_field": "per_ordered",
				"target_ref_field": "stock_qty",
				"target_field": "ordered_qty",
				"name": doc.name,
			},
			update_modified=True,
		)


@frappe.whitelist()
def append_material_request_items(mr_name: str, items_json: str) -> dict:
	"""向草稿状态 MR 追加明细行。items_json 为 JSON 数组，每项含 item_code、qty、schedule_date、description。"""
	if not mr_name:
		frappe.throw(_("物料需求单名称不能为空"))
	data = json.loads(items_json) if isinstance(items_json, str) else items_json
	if not data:
		frappe.throw(_("明细不能为空"))

	mr = frappe.get_doc("Material Request", mr_name)
	mr.check_permission("write")
	if mr.docstatus != 0:
		frappe.throw(_("仅草稿状态可追加明细，当前 docstatus={0}").format(mr.docstatus))

	schedule_date = mr.schedule_date or frappe.utils.add_days(mr.transaction_date, 14)
	for d in data:
		if not d.get("item_code"):
			continue
		mr.append("items", {
			"item_code": d.get("item_code"),
			"qty": flt(d.get("qty"), 1) or 1,
			"schedule_date": d.get("schedule_date") or schedule_date,
			"description": d.get("description") or "",
		})
	mr.save()
	frappe.db.commit()
	return {"name": mr.name, "appended": len(data)}


@frappe.whitelist()
def update_material_request_items(mr_name: str, trans_items: str) -> None:
	"""更新物料需求单明细（提交后）。trans_items 为 JSON 数组，每项含 docname、item_code、qty、schedule_date、warehouse、description 等。"""
	if not mr_name:
		frappe.throw(_("物料需求单名称不能为空"))

	data = json.loads(trans_items) if isinstance(trans_items, str) else trans_items
	if not data:
		frappe.throw(_("明细不能为空"))

	mr = frappe.get_doc("Material Request", mr_name)
	mr.check_permission("write")

	if not can_update_material_request_items(mr_name):
		frappe.throw(
			_("当前不允许变更此物料需求单的明细"),
			title=_("权限不足"),
		)

	updated_docnames = {d.get("docname") for d in data if d.get("docname")}

	# 校验待删除行：ordered_qty 必须为 0
	for item in mr.items:
		if item.name not in updated_docnames:
			if flt(item.ordered_qty) > 0:
				frappe.throw(
					_("行 #{0}：物料 {1} 已下单数量为 {2}，需先在关联采购单中处理后再删除。").format(
						item.idx, item.item_code, item.ordered_qty
					),
					title=_("无法删除"),
				)

	# 构建新的 items 列表
	existing_map = {d.name: d for d in mr.items}
	new_items = []
	seen_docnames = set()

	for idx, d in enumerate(data):
		if not d.get("item_code"):
			continue

		docname = d.get("docname")
		new_qty = flt(d.get("qty"))
		if new_qty <= 0:
			frappe.throw(
				_("行 #{0}：物料 {1} 的数量必须大于 0。").format(idx + 1, d.get("item_code")),
				title=_("数量无效"),
			)

		if docname and docname in existing_map:
			child = existing_map[docname]
			ordered_qty = flt(child.ordered_qty)
			if new_qty < ordered_qty:
				frappe.throw(
					_("行 #{0}：物料 {1} 的数量不能小于已下单数量 {2}。").format(
						idx + 1, child.item_code, ordered_qty
					),
					title=_("数量无效"),
				)
			child.qty = new_qty
			child.schedule_date = d.get("schedule_date") or mr.schedule_date
			child.warehouse = d.get("warehouse") or mr.set_warehouse
			child.description = d.get("description") or ""
			if "custom_supplier_provides_drawing" in d:
				child.custom_supplier_provides_drawing = 1 if d.get("custom_supplier_provides_drawing") else 0
			if d.get("uom"):
				child.uom = d.get("uom")
			if flt(d.get("conversion_factor")) > 0:
				child.conversion_factor = flt(d.get("conversion_factor"))
			child.stock_qty = flt(child.qty) * flt(child.conversion_factor)
			child.idx = idx + 1
			new_items.append(child)
			seen_docnames.add(docname)
		else:
			# 新增行
			mr.check_permission("create")
			child = _make_new_mr_item(mr, d, idx + 1)
			new_items.append(child)

	mr.items = new_items
	mr.flags.ignore_validate_update_after_submit = True  # 跳过 Frappe 默认校验，由 validate_mr_item_qty_on_update 做业务校验
	mr._action = "update_after_submit"
	mr.save()


def _make_new_mr_item(mr, trans_item: dict, idx: int):
	"""根据 trans_item 创建新的 Material Request Item 行。"""
	item = frappe.get_doc("Item", trans_item.get("item_code"))
	child = frappe.new_doc("Material Request Item", parent_doc=mr, parentfield="items")
	child.idx = idx
	child.item_code = item.item_code
	child.item_name = item.item_name
	child.description = trans_item.get("description") or item.description or ""
	child.item_group = item.item_group
	child.qty = flt(trans_item.get("qty"))
	child.uom = trans_item.get("uom") or item.stock_uom
	child.stock_uom = item.stock_uom

	from erpnext.stock.get_item_details import get_conversion_factor

	conv = get_conversion_factor(item.item_code, child.uom)
	child.conversion_factor = flt(trans_item.get("conversion_factor")) or flt(conv.get("conversion_factor")) or 1
	child.stock_qty = flt(child.qty) * flt(child.conversion_factor)
	child.schedule_date = trans_item.get("schedule_date") or mr.schedule_date
	child.warehouse = trans_item.get("warehouse") or mr.set_warehouse
	if "custom_supplier_provides_drawing" in trans_item:
		child.custom_supplier_provides_drawing = 1 if trans_item.get("custom_supplier_provides_drawing") else 0
	return child

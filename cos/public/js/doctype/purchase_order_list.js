// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

/** 采购订单明细（子表）物料名称：仅含关键字（LIKE %…%）筛选 */
const PO_ITEM_DOCTYPE = "Purchase Order Item";
const PO_ITEM_NAME_FIELD = "item_name";

function build_po_item_name_filter(value) {
	const v = (value || "").trim();
	if (!v) {
		return null;
	}
	let like_val = v;
	if (typeof like_val === "string" && !like_val.includes("%")) {
		like_val = "%" + like_val + "%";
	}
	return [PO_ITEM_DOCTYPE, PO_ITEM_NAME_FIELD, "like", like_val];
}

// 必须合并 ERPNext 自带配置：整对象赋值会丢掉 get_indicator / add_fields，
// 状态列会退化成仅显示「已提交」，橙色「待入库与开票」等徽章不再出现。
const _po_list_existing = frappe.listview_settings["Purchase Order"] || {};
const _po_list_erpnext_onload = _po_list_existing.onload;

frappe.listview_settings["Purchase Order"] = Object.assign({}, _po_list_existing, {
	onload: function (listview) {
		if (typeof _po_list_erpnext_onload === "function") {
			_po_list_erpnext_onload(listview);
		}
		frappe.model.with_doctype(PO_ITEM_DOCTYPE, function () {
			// 不可 page.add_field：伪字段会进入 get_standard_filters。
			// 子表条件通过 filter_area 维护，与「过滤条件」弹层、URL 解析共用同一套 filters。
			listview.page.show_form();

			const $section = listview.page.page_form.find(".standard-filter-section");
			const parent = $section.length ? $section : listview.page.page_form;

			const item_name_ctrl = frappe.ui.form.make_control({
				df: {
					fieldname: "cos_po_item_name_search",
					fieldtype: "Data",
					label: __("明细物料名称"),
					placeholder: __("含关键字"),
					condition: "like",
				},
				parent: parent,
				only_input: true,
			});
			item_name_ctrl.refresh();
			if (!item_name_ctrl.$input) {
				item_name_ctrl.make_input();
			}

			$(item_name_ctrl.wrapper)
				.addClass("col-md-2")
				.attr("title", __("按采购订单明细行物料名称模糊筛选"));

			const name_field = listview.page.fields_dict && listview.page.fields_dict.name;
			if (name_field && name_field.$wrapper && name_field.$wrapper.length) {
				$(item_name_ctrl.wrapper).insertAfter(name_field.$wrapper);
			} else if ($section.length) {
				$(item_name_ctrl.wrapper).prependTo($section);
			}

			const apply_po_item_name_filter = function () {
				const next = build_po_item_name_filter(item_name_ctrl.get_value());
				const fa = listview.filter_area;
				if (!fa || !fa.remove) {
					return;
				}
				listview.start = 0;
				const after_remove = fa.remove(PO_ITEM_NAME_FIELD);
				const p = after_remove && typeof after_remove.then === "function" ? after_remove : Promise.resolve();
				p.then(() => {
					if (next) {
						return fa.add(next);
					}
					return listview.refresh();
				});
			};

			const debounced_apply = frappe.utils.debounce(apply_po_item_name_filter, 400);

			if (item_name_ctrl.$input) {
				item_name_ctrl.$input.on("input", debounced_apply);
				item_name_ctrl.$input.on("keydown", function (e) {
					if (e.key === "Enter") {
						e.preventDefault();
						if (!debounced_apply.flush()) {
							apply_po_item_name_filter();
						}
					}
				});
			}
		});
	},
});

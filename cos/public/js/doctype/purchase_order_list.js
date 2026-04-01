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

frappe.listview_settings["Purchase Order"] = {
	onload: function (listview) {
		frappe.model.with_doctype(PO_ITEM_DOCTYPE, function () {
			// 不可 page.add_field：伪字段会进入 get_standard_filters。
			// 子表条件在 get_filters_for_args 中追加（与 reportview 一致）。
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

			const orig_get_filters = listview.get_filters_for_args.bind(listview);
			listview.get_filters_for_args = function () {
				const filters = orig_get_filters();
				const extra = build_po_item_name_filter(item_name_ctrl.get_value());
				if (!extra) {
					return filters;
				}
				const exists = filters.some(
					(f) =>
						f.length >= 4 &&
						f[0] === PO_ITEM_DOCTYPE &&
						f[1] === PO_ITEM_NAME_FIELD &&
						f[2] === extra[2] &&
						f[3] === extra[3]
				);
				if (exists) {
					return filters;
				}
				return filters.concat([extra]);
			};

			const debounced_refresh = frappe.utils.debounce(function () {
				listview.start = 0;
				listview.refresh();
			}, 400);

			if (item_name_ctrl.$input) {
				item_name_ctrl.$input.on("input", debounced_refresh);
				item_name_ctrl.$input.on("keydown", function (e) {
					if (e.key === "Enter") {
						e.preventDefault();
						if (!debounced_refresh.flush()) {
							listview.start = 0;
							listview.refresh();
						}
					}
				});
			}
		});
	},
};

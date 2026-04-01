// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

/** 采购订单明细（子表）物料名称模糊筛选，注入列表页工具栏 */
const PO_ITEM_DOCTYPE = "Purchase Order Item";
const PO_ITEM_NAME_FIELD = "item_name";

function build_po_item_name_filter(value) {
	const v = (value || "").trim();
	if (!v) {
		return null;
	}
	return [PO_ITEM_DOCTYPE, PO_ITEM_NAME_FIELD, "like", "%" + v + "%"];
}

frappe.listview_settings["Purchase Order"] = {
	onload: function (listview) {
		const apply_item_name_filter = function () {
			const field = listview.page.fields_dict.cos_po_item_name_search;
			const raw = field ? field.get_value() : "";
			const next_filter = build_po_item_name_filter(raw);

			listview.filter_area.remove(PO_ITEM_NAME_FIELD).then(() => {
				if (next_filter) {
					listview.filter_area.add(next_filter);
				} else {
					listview.refresh();
				}
			});
		};

		const debounced_apply = frappe.utils.debounce(apply_item_name_filter, 400);

		const field = listview.page.add_field({
			fieldname: "cos_po_item_name_search",
			fieldtype: "Data",
			label: __("明细物料名称"),
			placeholder: __("模糊匹配子表物料名称"),
		});

		if (field && field.$input) {
			field.$input.on("input", debounced_apply);
			field.$input.on("keydown", function (e) {
				if (e.key === "Enter") {
					e.preventDefault();
					if (!debounced_apply.flush()) {
						apply_item_name_filter();
					}
				}
			});
		}
	},
};

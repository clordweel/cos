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
		// 不可使用 page.add_field：有值的字段会进入 get_standard_filters 并作为主表字段发给服务端，
		// cos_po_item_name_search 并非 Purchase Order 字段，会触发「查询过滤条件字段无效」。
		listview.page.show_form();

		const apply_item_name_filter = function () {
			const raw = item_name_ctrl ? item_name_ctrl.get_value() : "";
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

		const item_name_ctrl = frappe.ui.form.make_control({
			df: {
				fieldname: "cos_po_item_name_search",
				fieldtype: "Data",
				label: __("明细物料名称"),
				placeholder: __("模糊匹配子表物料名称"),
			},
			parent: listview.page.page_form,
			only_input: true,
		});
		item_name_ctrl.refresh();
		if (!item_name_ctrl.$input) {
			item_name_ctrl.make_input();
		}
		$(item_name_ctrl.wrapper)
			.addClass("col-md-2")
			.attr("title", __("按采购订单明细行物料名称模糊筛选，不写入主表字段"))
			.tooltip({ delay: { show: 600, hide: 100 }, trigger: "hover" });

		if (item_name_ctrl.$input) {
			item_name_ctrl.$input.on("input", debounced_apply);
			item_name_ctrl.$input.on("keydown", function (e) {
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

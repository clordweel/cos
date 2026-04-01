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
		frappe.model.with_doctype(PO_ITEM_DOCTYPE, function () {
			// 不可使用 page.add_field：有值的字段会进入 get_standard_filters 并作为主表字段发给服务端。
			// 不可依赖 filter_area.add(子表条件)：FilterGroup.push_new_filter 对子表行在部分环境下无法稳定加入，
			// 表现为列表请求不带子表筛选、界面「无反应」。改为覆写 get_filters_for_args，与 reportview 使用同一套 filters。
			listview.page.show_form();

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
				.attr("title", __("按采购订单明细行物料名称模糊筛选"))
				.tooltip({ delay: { show: 600, hide: 100 }, trigger: "hover" });
			// 置于列表工具栏表单最前（默认 append 会在 ID/标准筛选之后）
			$(item_name_ctrl.wrapper).prependTo(listview.page.page_form);

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

			const refresh_filtered = function () {
				listview.start = 0;
				listview.refresh();
			};

			const debounced_refresh = frappe.utils.debounce(refresh_filtered, 400);

			if (item_name_ctrl.$input) {
				item_name_ctrl.$input.on("input", debounced_refresh);
				item_name_ctrl.$input.on("keydown", function (e) {
					if (e.key === "Enter") {
						e.preventDefault();
						if (!debounced_refresh.flush()) {
							refresh_filtered();
						}
					}
				});
			}
		});
	},
};

// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

/** 采购订单明细（子表）物料名称筛选：行为对齐列表「编号」等 Data 标准筛选项（等于 / 含关键词） */
const PO_ITEM_DOCTYPE = "Purchase Order Item";
const PO_ITEM_NAME_FIELD = "item_name";

function build_po_item_name_filter(value, match_type) {
	const v = (value || "").trim();
	if (!v) {
		return null;
	}
	const mt = match_type === "=" ? "=" : "like";
	if (mt === "=") {
		return [PO_ITEM_DOCTYPE, PO_ITEM_NAME_FIELD, "=", v.replace(/^%+|%+$/g, "")];
	}
	let like_val = v;
	if (typeof like_val === "string" && !like_val.includes("%")) {
		like_val = "%" + like_val + "%";
	}
	return [PO_ITEM_DOCTYPE, PO_ITEM_NAME_FIELD, "like", like_val];
}

/**
 * 对齐 frappe FilterArea.filter_field_with_match_type：输入框 + 等于/含关键词 下拉
 * 不写入 page.fields_dict，避免伪字段进入 get_standard_filters
 */
function attach_po_item_match_type_ui(field, listview) {
	setTimeout(function () {
		if (!field || !field.$wrapper) {
			return;
		}
		const $input = field.$wrapper.find("input").first();
		if (!$input.length || $input.closest(".input-group").length) {
			return;
		}

		field.df.match_type = field.df.match_type || field.df.condition || "like";

		const getIcon = function (match_type) {
			if (match_type === "=") {
				return frappe.utils.icon("equal");
			}
			return frappe.utils.icon("equal-approximately");
		};

		$input.wrap('<div class="input-group input-group-sm">');
		const $inputGroup = $input.parent();

		const $dd = $(`
			<div class="input-group-btn">
				<button type="button" class="btn btn-default btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"></button>
				<ul class="dropdown-menu dropdown-menu-right">
					<li><a class="dropdown-item" href="#" data-match-type="=">${__("Equals")}</a></li>
					<li><a class="dropdown-item" href="#" data-match-type="like">${__("Like")}</a></li>
				</ul>
			</div>
		`);
		$dd.find("button").first().html(getIcon(field.df.match_type));
		$inputGroup.append($dd);

		const $dropdown = $dd;
		$dropdown.find(".dropdown-item").on("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			$dropdown.find("button").dropdown("toggle");

			const new_type = $(e.currentTarget).data("match-type");
			const current_type = field.df.match_type || "like";
			if (new_type === current_type) {
				return;
			}

			field.df.match_type = new_type;
			$dropdown.find("button").first().html(getIcon(new_type));

			let val = field.get_value && field.get_value();
			if (new_type === "=" && val) {
				field.set_value(String(val).replace(/^%+|%+$/g, ""));
			}

			if (val) {
				listview.start = 0;
				listview.refresh();
			}
		});
	}, 100);
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
					placeholder: __("明细物料名称"),
					condition: "like",
				},
				parent: parent,
				only_input: true,
			});
			item_name_ctrl.refresh();
			if (!item_name_ctrl.$input) {
				item_name_ctrl.make_input();
			}
			item_name_ctrl.df.match_type = "like";

			$(item_name_ctrl.wrapper)
				.addClass("col-md-2")
				.attr("title", __("按采购订单明细行物料名称筛选"));

			const name_field = listview.page.fields_dict && listview.page.fields_dict.name;
			if (name_field && name_field.$wrapper && name_field.$wrapper.length) {
				$(item_name_ctrl.wrapper).insertAfter(name_field.$wrapper);
			} else if ($section.length) {
				$(item_name_ctrl.wrapper).prependTo($section);
			}

			attach_po_item_match_type_ui(item_name_ctrl, listview);

			const orig_get_filters = listview.get_filters_for_args.bind(listview);
			listview.get_filters_for_args = function () {
				const filters = orig_get_filters();
				const extra = build_po_item_name_filter(
					item_name_ctrl.get_value(),
					item_name_ctrl.df.match_type || "like"
				);
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

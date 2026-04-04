// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

/** 采购订单明细（子表）物料名称：仅含关键字（LIKE %…%）筛选，快捷方式等价于在「过滤条件」中新增一行 */
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

/** 从过滤条件中解析子表 item_name 的 like/not like 值，去掉首尾 % 供快捷框展示 */
function parse_po_item_name_display_from_filters(filters) {
	if (!filters || !filters.length) {
		return "";
	}
	for (const f of filters) {
		if (
			f.length >= 4 &&
			f[0] === PO_ITEM_DOCTYPE &&
			f[1] === PO_ITEM_NAME_FIELD &&
			(f[2] === "like" || f[2] === "not like") &&
			typeof f[3] === "string"
		) {
			return f[3].replace(/^%+|%+$/g, "");
		}
	}
	return "";
}

/**
 * FilterGroup 在带「过滤条件」按钮时，this.wrapper 仅在首次打开 popover 后才指向 .filter-popover。
 * 在此之前调用 add_filter 会导致 Filter 的 parent 为空，行不会出现在右侧过滤面板中。
 */
function ensure_po_filter_popover_wrapper(listview) {
	if (listview._cos_po_filter_popover_ready) {
		return Promise.resolve();
	}
	const fl = listview.filter_list;
	if (!fl || !fl.filter_button) {
		listview._cos_po_filter_popover_ready = true;
		return Promise.resolve();
	}
	if (fl.wrapper) {
		listview._cos_po_filter_popover_ready = true;
		return Promise.resolve();
	}
	return new Promise((resolve) => {
		const done = () => {
			listview._cos_po_filter_popover_ready = true;
			resolve();
		};
		fl.filter_button.one("shown.bs.popover", () => {
			fl.filter_button.popover("hide");
			done();
		});
		fl.filter_button.popover("show");
	});
}

// 必须合并 ERPNext 自带配置：整对象赋值会丢掉 get_indicator / add_fields，
// 状态列会退化成仅显示「已提交」，橙色「待入库与开票」等徽章不再出现。
const _po_list_existing = frappe.listview_settings["Purchase Order"] || {};
const _po_list_erpnext_onload = _po_list_existing.onload;
const _po_list_erpnext_refresh = _po_list_existing.refresh;

frappe.listview_settings["Purchase Order"] = Object.assign({}, _po_list_existing, {
	refresh: function (listview) {
		if (typeof _po_list_erpnext_refresh === "function") {
			_po_list_erpnext_refresh(listview);
		}
		if (listview._cos_sync_shortcut_from_filters) {
			listview._cos_sync_shortcut_from_filters();
		}
	},
	onload: function (listview) {
		if (typeof _po_list_erpnext_onload === "function") {
			_po_list_erpnext_onload(listview);
		}
		frappe.model.with_doctype(PO_ITEM_DOCTYPE, function () {
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
				.attr("title", __("快捷：等同于在「过滤条件」中添加「物料名称(采购订单明细)」含关键字；两侧会同步"));

			const name_field = listview.page.fields_dict && listview.page.fields_dict.name;
			if (name_field && name_field.$wrapper && name_field.$wrapper.length) {
				$(item_name_ctrl.wrapper).insertAfter(name_field.$wrapper);
			} else if ($section.length) {
				$(item_name_ctrl.wrapper).prependTo($section);
			}

			listview._cos_po_item_name_ctrl = item_name_ctrl;
			listview._cos_po_item_name_shortcut_focused = false;
			listview._cos_po_filter_apply_in_progress = false;

			listview._cos_sync_shortcut_from_filters = function () {
				if (listview._cos_po_filter_sync_in_progress) {
					return;
				}
				// 用户正在编辑快捷框时，不以过滤条件覆盖输入（避免删字后被旧条件写回）
				if (listview._cos_po_item_name_shortcut_focused) {
					return;
				}
				// 快捷框正在应用 remove/add/refresh 时，过滤列表可能尚未更新，同步会误把旧关键字写回
				if (listview._cos_po_filter_apply_in_progress) {
					return;
				}
				const fa = listview.filter_area;
				const ctrl = listview._cos_po_item_name_ctrl;
				if (!fa || !fa.filter_list || !ctrl) {
					return;
				}
				const filters = fa.filter_list.get_filters();
				const display = parse_po_item_name_display_from_filters(filters);
				const cur = (ctrl.get_value() || "").trim();
				if (cur === display.trim()) {
					return;
				}
				listview._cos_po_filter_sync_in_progress = true;
				try {
					ctrl.set_value(display);
				} finally {
					setTimeout(() => {
						listview._cos_po_filter_sync_in_progress = false;
					}, 50);
				}
			};

			const finish_po_item_apply = function () {
				listview._cos_po_filter_apply_in_progress = false;
			};

			const apply_po_item_name_filter = function () {
				if (listview._cos_po_filter_sync_in_progress) {
					return;
				}
				const next = build_po_item_name_filter(item_name_ctrl.get_value());
				const fa = listview.filter_area;
				if (!fa || !fa.remove) {
					return;
				}
				listview.start = 0;
				listview._cos_po_filter_apply_in_progress = true;
				ensure_po_filter_popover_wrapper(listview)
					.then(() => {
						const after_remove = fa.remove(PO_ITEM_NAME_FIELD);
						const p =
							after_remove && typeof after_remove.then === "function"
								? after_remove
								: Promise.resolve();
						return p.then(() => {
							if (next) {
								const added = fa.add(next[0], next[1], next[2], next[3]);
								return added && typeof added.then === "function" ? added : Promise.resolve();
							}
							return listview.refresh();
						});
					})
					.then(finish_po_item_apply)
					.catch(finish_po_item_apply);
			};

			const fl = listview.filter_list;
			if (fl && typeof fl.on_change === "function") {
				const orig_fl_on_change = fl.on_change;
				fl.on_change = function () {
					orig_fl_on_change.call(this);
					listview._cos_sync_shortcut_from_filters();
				};
			}

			const debounced_apply = frappe.utils.debounce(apply_po_item_name_filter, 400);
			/** 中文等 IME 组字过程中会触发 input，需等 compositionend 再筛选 */
			let po_item_name_ime_composing = false;

			if (item_name_ctrl.$input) {
				const $input = item_name_ctrl.$input;
				$input.on("focus", function () {
					listview._cos_po_item_name_shortcut_focused = true;
				});
				$input.on("blur", function () {
					listview._cos_po_item_name_shortcut_focused = false;
					if (po_item_name_ime_composing) {
						return;
					}
					if (!debounced_apply.flush()) {
						apply_po_item_name_filter();
					}
				});
				$input.on("compositionstart", function () {
					po_item_name_ime_composing = true;
				});
				$input.on("compositionend", function () {
					po_item_name_ime_composing = false;
					debounced_apply();
				});
				$input.on("input", function () {
					if (po_item_name_ime_composing) {
						return;
					}
					debounced_apply();
				});
				$input.on("keydown", function (e) {
					if (e.key !== "Enter") {
						return;
					}
					if (po_item_name_ime_composing) {
						return;
					}
					e.preventDefault();
					if (!debounced_apply.flush()) {
						apply_po_item_name_filter();
					}
				});
			}

			setTimeout(() => listview._cos_sync_shortcut_from_filters(), 0);
		});
	},
});

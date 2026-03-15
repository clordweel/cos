// Copyright (c) 2025, COS and contributors
// License: MIT. See license.txt
//
// 为 Frappe 表单子表（Grid）添加列宽拖拽调整功能，方便查看被截断的单元格内容。

(function () {
	const MIN_COL_WIDTH = 60;
	const STORAGE_PREFIX = "grid_col_";

	function get_storage_key(parent_doctype, child_doctype) {
		return STORAGE_PREFIX + parent_doctype + "_" + child_doctype;
	}

	function load_column_widths(parent_doctype, child_doctype) {
		try {
			const raw = localStorage.getItem(get_storage_key(parent_doctype, child_doctype));
			return raw ? JSON.parse(raw) : {};
		} catch {
			return {};
		}
	}

	function save_column_widths(parent_doctype, child_doctype, widths) {
		try {
			localStorage.setItem(
				get_storage_key(parent_doctype, child_doctype),
				JSON.stringify(widths)
			);
		} catch {
			// ignore
		}
	}

	function setup_column_resize(grid) {
		if (!grid.wrapper || !grid.df) return;

		const $grid_field = grid.wrapper;
		const $heading_row = $grid_field.find(".grid-heading-row .grid-row").first();
		const $cols = $heading_row.find(".grid-static-col[data-fieldname]");
		if (!$cols.length) return;

		const parent_doctype = grid.frm ? grid.frm.doctype : "";
		const child_doctype = grid.df.options || "";
		const saved_widths = parent_doctype && child_doctype ? load_column_widths(parent_doctype, child_doctype) : {};

		$cols.each(function () {
			const $col = $(this);
			const fieldname = $col.attr("data-fieldname");
			if (!fieldname || $col.find(".grid-col-resize-handle").length) return;

			const handle = $('<div class="grid-col-resize-handle" role="separator" aria-label="' + __("Resize column") + '"></div>');
			$col.append(handle);
			$col.css("position", "relative");

			const apply_width = (w) => {
				const width = Math.max(MIN_COL_WIDTH, Math.round(w));
				const flex = `0 0 ${width}px`;
				$grid_field.find('.grid-static-col[data-fieldname="' + fieldname + '"]').each(function () {
					$(this).css({
						minWidth: width + "px",
						flex: flex,
						width: width + "px",
					});
				});
			};

			if (saved_widths[fieldname] && saved_widths[fieldname] >= MIN_COL_WIDTH) {
				apply_width(saved_widths[fieldname]);
			}

			handle.on("mousedown", function (e) {
				e.preventDefault();
				e.stopPropagation();
				const start_x = e.pageX;
				const start_width = $col.outerWidth() || MIN_COL_WIDTH;

				const on_move = (ev) => {
					const dx = ev.pageX - start_x;
					apply_width(start_width + dx);
				};

				const on_up = () => {
					$(document).off("mousemove", on_move).off("mouseup", on_up);
					$("body").removeClass("grid-col-resizing").css("user-select", "");
					if (parent_doctype && child_doctype) {
						const to_save = {};
						$grid_field.find(".grid-heading-row .grid-static-col[data-fieldname]").each(function () {
							const fn = $(this).attr("data-fieldname");
							const w = $(this).outerWidth();
							if (fn && w >= MIN_COL_WIDTH) to_save[fn] = Math.round(w);
						});
						save_column_widths(parent_doctype, child_doctype, to_save);
					}
				};

				$("body").addClass("grid-col-resizing").css("user-select", "none");
				$(document).on("mousemove", on_move).on("mouseup", on_up);
			});
		});
	}

	let patch_done = false;

	function patch_single_grid(grid) {
		if (!grid || grid._cos_resize_patched) return;
		const original_refresh = grid.refresh.bind(grid);
		grid.refresh = function () {
			original_refresh.apply(this, arguments);
			setTimeout(() => setup_column_resize(this), 0);
		};
		grid._cos_resize_patched = true;
	}

	function patch_existing_forms() {
		try {
			const frm = frappe.cur_page?.page?.frm;
			if (frm && frm.grids) {
				frm.grids.forEach((g) => patch_single_grid(g));
			}
		} catch {
			// ignore
		}
	}

	function patch_grid_refresh() {
		if (patch_done) return true;
		const ControlTable = frappe.ui.form.ControlTable;
		if (!ControlTable || !ControlTable.prototype.make) return false;

		const original_make = ControlTable.prototype.make;
		ControlTable.prototype.make = function () {
			original_make.apply(this, arguments);
			patch_single_grid(this.grid);
		};
		patch_done = true;
		patch_existing_forms();
		return true;
	}

	$(document).on("app_ready", () => {
		if (!patch_grid_refresh()) {
			let attempts = 0;
			const id = setInterval(() => {
				if (patch_grid_refresh() || ++attempts >= 20) clearInterval(id);
			}, 500);
		}
	});
})();

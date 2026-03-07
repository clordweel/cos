// Copyright (c) COS and contributors
// 订单物料子表：表头点击列排序（升序/降序）+ 表头列拖拽调整列宽，列宽持久化到 localStorage

(function () {
	const STORAGE_KEY_PREFIX = "cos_grid_col_";
	const MIN_COL_WIDTH = 60;
	const DEFAULT_COL_WIDTH = 120;
	const RESIZE_HANDLE_CLASS = "cos-grid-col-resize-handle";
	const RESIZE_INIT_ATTR = "data-cos-resize-init";
	const SORT_ATTR = "data-cos-sort-init";

	// 订单类单据及其要启用排序+列宽的物料子表字段
	const ORDER_ITEM_GRID_FIELDS = [
		{ doctype: "Sales Order", fieldname: "items" },
		{ doctype: "Purchase Order", fieldname: "items" },
		{ doctype: "Delivery Note", fieldname: "items" },
		{ doctype: "Sales Invoice", fieldname: "items" },
		{ doctype: "Purchase Receipt", fieldname: "items" },
		{ doctype: "Quotation", fieldname: "items" },
		{ doctype: "Subcontracting Order", fieldname: "items" },
	];

	function getStorageKey(parent_doctype, table_fieldname, col_fieldname) {
		return `${STORAGE_KEY_PREFIX}${parent_doctype}_${table_fieldname}_${col_fieldname}`;
	}

	function getColumnWidth(parent_doctype, table_fieldname, col_fieldname) {
		try {
			const key = getStorageKey(parent_doctype, table_fieldname, col_fieldname);
			const w = localStorage.getItem(key);
			return w ? parseInt(w, 10) : null;
		} catch (e) {
			return null;
		}
	}

	function setColumnWidth(parent_doctype, table_fieldname, col_fieldname, widthPx) {
		try {
			const key = getStorageKey(parent_doctype, table_fieldname, col_fieldname);
			localStorage.setItem(key, String(widthPx));
		} catch (e) {
			// ignore
		}
	}

	// 使用 form_grid 作为查找范围，确保只影响表格区域
	function getGridContainer(grid) {
		return grid.form_grid && grid.form_grid.length ? grid.form_grid : grid.wrapper;
	}

	function applyWidthToColumn(container, fieldname, widthPx) {
		const w = Math.max(MIN_COL_WIDTH, widthPx);
		const style = {
			width: w + "px",
			minWidth: w + "px",
			maxWidth: w + "px",
			flex: "0 0 " + w + "px",
			boxSizing: "border-box",
		};
		container.find(".grid-static-col[data-fieldname='" + fieldname + "']").css(style);
	}

	function applySavedColumnWidths(grid, parent_doctype, table_fieldname) {
		if (!grid || !grid.visible_columns || grid.visible_columns.length === 0) return;
		const $container = getGridContainer(grid);
		// 防止行换行，保证列宽生效
		$container.find(".grid-heading-row .row, .grid-body .row").css("flexWrap", "nowrap");
		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;
			const saved = getColumnWidth(parent_doctype, table_fieldname, df.fieldname);
			if (saved) applyWidthToColumn($container, df.fieldname, saved);
		}
	}

	function setupResizeHandles(grid, parent_doctype, table_fieldname) {
		if (!grid || !grid.visible_columns || grid.visible_columns.length === 0) return;
		const $container = getGridContainer(grid);
		const $headingRow = $container.find(".grid-heading-row .grid-row:not(.filter-row)").first();
		if (!$headingRow.length) return;

		if ($headingRow.attr(RESIZE_INIT_ATTR)) return;
		$headingRow.attr(RESIZE_INIT_ATTR, "1");

		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;

			const $col = $headingRow.find(".grid-static-col[data-fieldname='" + df.fieldname + "']").first();
			if (!$col.length || $col.find("." + RESIZE_HANDLE_CLASS).length) continue;

			$col.css({ position: "relative", overflow: "visible" });
			const $handle = $(
				'<div class="' +
					RESIZE_HANDLE_CLASS +
					'" data-fieldname="' +
					df.fieldname +
					'" title="' +
					__("拖拽调整列宽") +
					'" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:col-resize;z-index:10;background:transparent;"></div>'
			);
			$col.append($handle);

			$handle.on("mousedown", function (e) {
				e.preventDefault();
				e.stopPropagation();
				const startX = e.pageX;
				const $cells = $container.find(".grid-static-col[data-fieldname='" + df.fieldname + "']");
				const firstEl = $cells.get(0);
				let startWidth = firstEl ? firstEl.getBoundingClientRect().width : DEFAULT_COL_WIDTH;

				function onMove(ev) {
					const dx = ev.pageX - startX;
					const newWidth = Math.max(MIN_COL_WIDTH, Math.round(startWidth + dx));
					$cells.css({
						width: newWidth + "px",
						minWidth: newWidth + "px",
						maxWidth: newWidth + "px",
						flex: "0 0 " + newWidth + "px",
						boxSizing: "border-box",
					});
				}

				function onUp(ev) {
					const dx = ev.pageX - startX;
					const finalWidth = Math.max(MIN_COL_WIDTH, Math.round(startWidth + dx));
					setColumnWidth(parent_doctype, table_fieldname, df.fieldname, finalWidth);
					$(document).off("mousemove", onMove).off("mouseup", onUp);
				}

				$(document).on("mousemove", onMove).on("mouseup", onUp);
			});
		}
	}

	// 表头点击列排序：整列升序/降序
	function compareVal(a, b, fieldname, df) {
		let va = a[fieldname];
		let vb = b[fieldname];
		const isNull = function (v) {
			return v === undefined || v === null || v === "";
		};
		if (isNull(va) && isNull(vb)) return 0;
		if (isNull(va)) return 1;
		if (isNull(vb)) return -1;
		const ft = (df && df.fieldtype) || "";
		if (["Int", "Float", "Currency", "Percent"].indexOf(ft) !== -1) {
			va = flt(va);
			vb = flt(vb);
			return va - vb;
		}
		if (["Date", "Datetime"].indexOf(ft) !== -1) {
			try {
				va = frappe.datetime.str_to_obj(va);
				vb = frappe.datetime.str_to_obj(vb);
				const ta = va && va.getTime ? va.getTime() : 0;
				const tb = vb && vb.getTime ? vb.getTime() : 0;
				return ta - tb;
			} catch (err) {
				return String(va).localeCompare(String(vb), undefined, { numeric: true });
			}
		}
		va = String(va);
		vb = String(vb);
		return va.localeCompare(vb, undefined, { numeric: true });
	}

	function setupColumnSort(grid, frm, table_fieldname) {
		if (!grid || !grid.wrapper || !frm || !grid.visible_columns || grid.visible_columns.length === 0) return;
		const $container = getGridContainer(grid);
		const $headingRow = $container.find(".grid-heading-row .grid-row:not(.filter-row)").first();
		if (!$headingRow.length) return;

		if (grid.wrapper.attr(SORT_ATTR)) return;
		grid.wrapper.attr(SORT_ATTR, "1");

		const sortState = { fieldname: null, asc: true };

		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;

			const $col = $headingRow.find(".grid-static-col[data-fieldname='" + df.fieldname + "']").first();
			if (!$col.length) continue;

			const $label = $col.find(".static-area").first();
			if (!$label.length) continue;

			$col.addClass("cos-grid-sortable-header").css("cursor", "pointer");
			$col.off("click.cos_sort").on("click.cos_sort", function (e) {
				e.preventDefault();
				e.stopPropagation();
				const asc = sortState.fieldname === df.fieldname ? !sortState.asc : true;
				sortState.fieldname = df.fieldname;
				sortState.asc = asc;

				const data = (frm.doc[table_fieldname] || []).slice();
				data.sort(function (a, b) {
					let cmp = compareVal(a, b, df.fieldname, df);
					return asc ? cmp : -cmp;
				});
				data.forEach(function (row, idx) {
					row.idx = idx + 1;
				});
				frm.doc[table_fieldname] = data;
				frm.refresh_field(table_fieldname);
			});
		}
	}

	function enhanceGrid(frm, entry) {
		const fieldname = entry.fieldname;
		const field = frm.fields_dict[fieldname];
		if (!field || !field.grid) return;
		const grid = field.grid;
		const parent_doctype = frm.doctype;

		if (!grid.visible_columns || grid.visible_columns.length === 0) return;

		// 表头列排序（升序/降序）
		setupColumnSort(grid, frm, fieldname);

		if (typeof frappe.is_mobile === "function" && frappe.is_mobile()) return;

		applySavedColumnWidths(grid, parent_doctype, fieldname);
		setupResizeHandles(grid, parent_doctype, fieldname);
	}

	function onFormRefresh(frm) {
		if (!frm || !frm.doctype) return;
		const entries = ORDER_ITEM_GRID_FIELDS.filter(function (e) {
			return e.doctype === frm.doctype;
		});
		if (entries.length === 0) return;

		setTimeout(function () {
			entries.forEach(function (entry) {
				enhanceGrid(frm, entry);
			});
		}, 150);
	}

	$(document).on("grid-make-sortable", function (_ev, frm) {
		if (!frm || !frm.doctype) return;
		const entries = ORDER_ITEM_GRID_FIELDS.filter(function (e) {
			return e.doctype === frm.doctype;
		});
		if (entries.length === 0) return;
		setTimeout(function () {
			entries.forEach(function (entry) {
				enhanceGrid(frm, entry);
			});
		}, 80);
	});

	frappe.ui.form.on("Form", {
		refresh: function (frm) {
			onFormRefresh(frm);
		},
	});
})();

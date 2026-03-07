// Copyright (c) COS and contributors
// 订单物料子表：行排序（依赖 Frappe 已有） + 表头列拖拽调整列宽，列宽持久化到 localStorage

(function () {
	const STORAGE_KEY_PREFIX = "cos_grid_col_";
	const MIN_COL_WIDTH = 60;
	const DEFAULT_COL_WIDTH = 120;
	const RESIZE_HANDLE_CLASS = "cos-grid-col-resize-handle";
	const RESIZE_INIT_ATTR = "data-cos-resize-init";

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

	function applyWidthToColumn($wrapper, fieldname, widthPx) {
		const w = Math.max(MIN_COL_WIDTH, widthPx);
		$wrapper.find(".grid-static-col[data-fieldname='" + fieldname + "']").css({
			width: w + "px",
			minWidth: w + "px",
			maxWidth: w + "px",
			flex: "0 0 " + w + "px",
		});
	}

	function applySavedColumnWidths(grid, parent_doctype, table_fieldname) {
		if (!grid || !grid.wrapper || !grid.visible_columns || grid.visible_columns.length === 0) return;
		const $wrapper = grid.wrapper;
		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;
			const saved = getColumnWidth(parent_doctype, table_fieldname, df.fieldname);
			if (saved) applyWidthToColumn($wrapper, df.fieldname, saved);
		}
	}

	function setupResizeHandles(grid, parent_doctype, table_fieldname) {
		if (!grid || !grid.wrapper || !grid.visible_columns || grid.visible_columns.length === 0) return;
		const $wrapper = grid.wrapper;
		// 表头第一行（非 filter-row）的列
		const $headingRow = $wrapper.find(".grid-heading-row .grid-row:not(.filter-row)").first();
		if (!$headingRow.length) return;

		// 避免重复初始化
		if ($headingRow.attr(RESIZE_INIT_ATTR)) return;
		$headingRow.attr(RESIZE_INIT_ATTR, "1");

		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;

			const $col = $headingRow.find(".grid-static-col[data-fieldname='" + df.fieldname + "']").first();
			if (!$col.length) continue;

			// 已有手柄则跳过
			if ($col.find("." + RESIZE_HANDLE_CLASS).length) continue;

			const $handle = $(
				'<div class="' +
					RESIZE_HANDLE_CLASS +
					'" data-fieldname="' +
					df.fieldname +
					'" title="' +
					__("拖拽调整列宽") +
					'" style="position:absolute;right:0;top:0;bottom:0;width:6px;cursor:col-resize;z-index:2;"></div>'
			);
			$col.css("position", "relative").append($handle);

			$handle.on("mousedown", function (e) {
				e.preventDefault();
				e.stopPropagation();
				const startX = e.pageX;
				const $cells = $wrapper.find(".grid-static-col[data-fieldname='" + df.fieldname + "']");
				const firstWidth = $cells.length ? $cells.first().outerWidth() : DEFAULT_COL_WIDTH;
				let startWidth = firstWidth;

				function onMove(ev) {
					const dx = ev.pageX - startX;
					const newWidth = Math.max(MIN_COL_WIDTH, startWidth + dx);
					$cells.css({
						width: newWidth + "px",
						minWidth: newWidth + "px",
						maxWidth: newWidth + "px",
						flex: "0 0 " + newWidth + "px",
					});
				}

				function onUp(ev) {
					const dx = ev.pageX - startX;
					const finalWidth = Math.max(MIN_COL_WIDTH, startWidth + dx);
					setColumnWidth(parent_doctype, table_fieldname, df.fieldname, finalWidth);
					$(document).off("mousemove", onMove).off("mouseup", onUp);
				}

				$(document).on("mousemove", onMove).on("mouseup", onUp);
			});
		}
	}

	function enhanceGrid(frm, entry) {
		const fieldname = entry.fieldname;
		const field = frm.fields_dict[fieldname];
		if (!field || !field.grid) return;
		const grid = field.grid;
		const parent_doctype = frm.doctype;

		// 确保 visible_columns 已就绪（grid.refresh 后会有）
		if (!grid.visible_columns || grid.visible_columns.length === 0) return;

		// 移动端不启用列宽拖拽
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

		// 在 grid 渲染后再应用（refresh 后 DOM 可能尚未完全更新）
		setTimeout(function () {
			entries.forEach(function (entry) {
				enhanceGrid(frm, entry);
			});
		}, 100);
	}

	// 监听 grid 渲染完成，以便分页/刷新后再次应用列宽
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
		}, 50);
	});

	// Form refresh 时统一处理
	frappe.ui.form.on("Form", {
		refresh: function (frm) {
			onFormRefresh(frm);
		},
	});
})();

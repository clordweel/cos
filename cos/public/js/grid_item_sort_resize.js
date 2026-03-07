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

	// 使用 form_grid 作为查找范围
	function getGridContainer(grid) {
		return grid.form_grid && grid.form_grid.length ? grid.form_grid : grid.wrapper;
	}

	// 每个 grid 的 CSS 作用域 id（用于注入 !important 列宽规则，覆盖 Bootstrap/Frappe）
	const GRID_ID_ATTR = "data-cos-grid-id";
	const STYLE_ID = "cos-grid-col-widths";
	const widthRules = {}; // { "Sales Order_items": { "item_code": 150, ... }, ... }

	function getGridScopeId(parent_doctype, table_fieldname) {
		return parent_doctype + "_" + table_fieldname;
	}

	function ensureStyleElement() {
		let el = document.getElementById(STYLE_ID);
		if (!el) {
			el = document.createElement("style");
			el.id = STYLE_ID;
			document.head.appendChild(el);
		}
		return el;
	}

	function writeWidthRulesToStyle() {
		const style = ensureStyleElement();
		const lines = [];
		Object.keys(widthRules).forEach(function (scopeId) {
			const cols = widthRules[scopeId];
			Object.keys(cols).forEach(function (fieldname) {
				const w = cols[fieldname];
				const sel =
					".grid-field[" +
					GRID_ID_ATTR +
					'="' +
					scopeId +
					'"] .grid-static-col[data-fieldname="' +
					fieldname +
					'"]';
				lines.push(
					sel +
						" { width: " +
						w +
						"px !important; min-width: " +
						w +
						"px !important; max-width: " +
						w +
						"px !important; flex: 0 0 " +
						w +
						"px !important; box-sizing: border-box !important; }"
				);
			});
		});
		style.textContent = lines.join("\n");
	}

	function setColumnWidthRule(parent_doctype, table_fieldname, col_fieldname, widthPx) {
		const scopeId = getGridScopeId(parent_doctype, table_fieldname);
		if (!widthRules[scopeId]) widthRules[scopeId] = {};
		widthRules[scopeId][col_fieldname] = Math.max(MIN_COL_WIDTH, widthPx);
		writeWidthRulesToStyle();
	}

	function applySavedColumnWidths(grid, parent_doctype, table_fieldname) {
		if (!grid) return;
		if (!grid.visible_columns || grid.visible_columns.length === 0) {
			if (typeof grid.setup_visible_columns === "function") grid.setup_visible_columns();
			if (!grid.visible_columns || grid.visible_columns.length === 0) return;
		}
		const scopeId = getGridScopeId(parent_doctype, table_fieldname);
		if (!grid.wrapper || !grid.wrapper.length) return;
		grid.wrapper.attr(GRID_ID_ATTR, scopeId);

		const $container = getGridContainer(grid);
		$container.find(".grid-heading-row .row, .grid-body .row").css("flexWrap", "nowrap");

		for (let i = 0; i < grid.visible_columns.length; i++) {
			const df = grid.visible_columns[i][0];
			if (!df || !df.fieldname) continue;
			const saved = getColumnWidth(parent_doctype, table_fieldname, df.fieldname);
			if (saved) setColumnWidthRule(parent_doctype, table_fieldname, df.fieldname, saved);
		}
	}

	function setupResizeHandles(grid, parent_doctype, table_fieldname) {
		if (!grid) return;
		if (!grid.visible_columns || grid.visible_columns.length === 0) {
			if (typeof grid.setup_visible_columns === "function") grid.setup_visible_columns();
			if (!grid.visible_columns || grid.visible_columns.length === 0) return;
		}
		const $container = getGridContainer(grid);
		// 表头行：第一个包含 .grid-static-col[data-fieldname] 的 .grid-row（不依赖 filter-row 挂在哪一层）
		const $headingRow = $container
			.find(".grid-heading-row .grid-row")
			.filter(function () {
				return $(this).find(".grid-static-col[data-fieldname]").length > 0;
			})
			.first();
		if (!$headingRow.length) return;

		if ($headingRow.attr(RESIZE_INIT_ATTR)) return;
		$headingRow.attr(RESIZE_INIT_ATTR, "1");

		if (!grid.wrapper || !grid.wrapper.length) return;
		grid.wrapper.attr(GRID_ID_ATTR, getGridScopeId(parent_doctype, table_fieldname));

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
					'" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:col-resize;z-index:10;background:rgba(0,120,212,0.2);"></div>'
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
					setColumnWidthRule(parent_doctype, table_fieldname, df.fieldname, newWidth);
				}

				function onUp(ev) {
					const dx = ev.pageX - startX;
					const finalWidth = Math.max(MIN_COL_WIDTH, Math.round(startWidth + dx));
					setColumnWidth(parent_doctype, table_fieldname, df.fieldname, finalWidth);
					setColumnWidthRule(parent_doctype, table_fieldname, df.fieldname, finalWidth);
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

		if (!grid.visible_columns || grid.visible_columns.length === 0) {
			if (typeof grid.setup_visible_columns === "function") grid.setup_visible_columns();
			if (!grid.visible_columns || grid.visible_columns.length === 0) return;
		}

		// 表头列排序（升序/降序）
		setupColumnSort(grid, frm, fieldname);

		if (typeof frappe.is_mobile === "function" && frappe.is_mobile()) return;

		applySavedColumnWidths(grid, parent_doctype, fieldname);
		setupResizeHandles(grid, parent_doctype, fieldname);
	}

	function runEnhanceForForm(frm) {
		if (!frm || !frm.doctype) return;
		const entries = ORDER_ITEM_GRID_FIELDS.filter(function (e) {
			return e.doctype === frm.doctype;
		});
		if (entries.length === 0) return;
		entries.forEach(function (entry) {
			enhanceGrid(frm, entry);
		});
	}

	function onFormRefresh(frm) {
		if (!frm || !frm.doctype) return;
		const entries = ORDER_ITEM_GRID_FIELDS.filter(function (e) {
			return e.doctype === frm.doctype;
		});
		if (entries.length === 0) return;
		// 多档延迟 + 点击表单时再试一次，应对 grid 在折叠区/tab 中晚渲染
		[100, 450, 1000].forEach(function (ms) {
			setTimeout(function () {
				runEnhanceForForm(frm);
			}, ms);
		});
		// 用户首次点击表单区域时再跑一次（仅一次）
		if (!frm.wrapper || !frm.wrapper.length) return;
		frm.wrapper.off("click.cos_grid_enhance").on("click.cos_grid_enhance", function () {
			frm.wrapper.off("click.cos_grid_enhance");
			setTimeout(function () {
				runEnhanceForForm(frm);
			}, 50);
		});
	}

	$(document).on("grid-make-sortable", function (_ev, frm) {
		if (!frm || !frm.doctype) return;
		setTimeout(function () {
			runEnhanceForForm(frm);
		}, 50);
	});

	frappe.ui.form.on("Form", {
		refresh: function (frm) {
			onFormRefresh(frm);
		},
	});

	// 兜底：不依赖 Form refresh 时机，轮询当前表单并在发现未增强的 grid 时补跑（应对脚本晚加载或 refresh 先于脚本）
	var pollCount = 0;
	var pollMax = 12;
	var pollInterval = setInterval(function () {
		pollCount++;
		if (pollCount > pollMax) {
			clearInterval(pollInterval);
			return;
		}
		var frm = frappe.cur_frm;
		if (!frm || !frm.doctype) return;
		var entries = ORDER_ITEM_GRID_FIELDS.filter(function (e) {
			return e.doctype === frm.doctype;
		});
		if (entries.length === 0) return;
		var field = frm.fields_dict && frm.fields_dict[entries[0].fieldname];
		if (!field || !field.grid) return;
		var grid = field.grid;
		if (!grid.wrapper || !grid.wrapper.length) return;
		if (grid.wrapper.attr(GRID_ID_ATTR)) return;
		runEnhanceForForm(frm);
	}, 500);

	window.__cos_grid_resize_loaded = true;
})();

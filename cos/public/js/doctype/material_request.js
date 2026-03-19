// Copyright (c) 2025, COS and contributors
// License: MIT. See license.txt

frappe.provide("cos.utils");

// 兼容 ERPNext v16：prevent_past_schedule_dates 可能不存在，补丁避免 refresh 报错导致订单变更按钮不显示
frappe.provide("erpnext.buying");
if (typeof erpnext.buying.prevent_past_schedule_dates !== "function") {
	erpnext.buying.prevent_past_schedule_dates = function () {};
}

frappe.ui.form.on("Material Request", {
	refresh: function (frm) {
		if (!frm.doc.name || frm.doc.__islocal) return;
		if (frm.doc.docstatus !== 1) return;
		if (["Stopped", "Cancelled"].includes(frm.doc.status)) return;
		if (!frm.has_perm("write")) return;

		frm.add_custom_button(__("Update Items"), () => {
			cos.utils.update_material_request_items_dialog(frm);
		});
	},
});

cos.utils.update_material_request_items_dialog = function (frm) {
	const child_meta = frappe.get_meta("Material Request Item");
	const get_precision = (fieldname) => {
		const f = child_meta.fields.find((x) => x.fieldname === fieldname);
		return f ? f.precision : 2;
	};

	const data = frm.doc.items.map((d) => ({
		docname: d.name,
		name: d.name,
		item_code: d.item_code,
		item_name: d.item_name,
		schedule_date: d.schedule_date,
		conversion_factor: d.conversion_factor,
		qty: d.qty,
		uom: d.uom,
		warehouse: d.warehouse,
		description: d.description || "",
		custom_supplier_provides_drawing: d.custom_supplier_provides_drawing || 0,
	}));

	const fields = [
		{ fieldtype: "Data", fieldname: "docname", read_only: 1, hidden: 1 },
		{
			fieldtype: "Link",
			fieldname: "item_code",
			options: "Item",
			in_list_view: 1,
			label: __("Item Code"),
			get_query: () => ({
				query: "erpnext.controllers.queries.item_query",
				filters: { is_purchase_item: 1 },
			}),
			onchange: function () {
				const me = this;
				if (!me.doc.item_code) return;
				frappe.call({
					method: "erpnext.stock.get_item_details.get_item_details",
					args: {
						doc: frm.doc,
						ctx: {
							item_code: me.doc.item_code,
							set_warehouse: frm.doc.set_warehouse,
							company: frm.doc.company,
							doctype: "Material Request",
							name: frm.doc.name,
							qty: me.doc.qty || 1,
							buying_price_list: frm.doc.buying_price_list,
						},
					},
					callback: (r) => {
						if (r.message) {
							me.doc.item_name = r.message.item_name;
							me.doc.uom = r.message.stock_uom || r.message.uom;
							me.doc.conversion_factor = r.message.conversion_factor || 1;
							me.doc.warehouse = r.message.warehouse || frm.doc.set_warehouse;
							me.doc.description = r.message.description || "";
							if (r.message.custom_supplier_provides_drawing !== undefined) {
								me.doc.custom_supplier_provides_drawing = r.message.custom_supplier_provides_drawing;
							}
							dialog.fields_dict.trans_items.grid.refresh();
						}
					},
				});
			},
		},
		{ fieldtype: "Data", fieldname: "item_name", label: __("Item Name"), read_only: 1, in_list_view: 1 },
		{
			fieldtype: "Float",
			fieldname: "qty",
			label: __("Qty"),
			in_list_view: 1,
			reqd: 1,
			precision: get_precision("qty"),
		},
		{
			fieldtype: "Link",
			fieldname: "uom",
			options: "UOM",
			label: __("UOM"),
			in_list_view: 1,
			reqd: 1,
		},
		{
			fieldtype: "Date",
			fieldname: "schedule_date",
			label: __("Required By"),
			in_list_view: 1,
			reqd: 1,
		},
		{
			fieldtype: "Link",
			fieldname: "warehouse",
			options: "Warehouse",
			label: __("Warehouse"),
			in_list_view: 1,
			get_query: () => ({ filters: { company: frm.doc.company, is_group: 0 } }),
		},
		{ fieldtype: "Small Text", fieldname: "description", label: __("Description") },
		{
			fieldtype: "Check",
			fieldname: "custom_supplier_provides_drawing",
			label: __("是否供应商提供图纸"),
			in_list_view: 1,
		},
	];

	const dialog = new frappe.ui.Dialog({
		title: __("Update Items"),
		size: "extra-large",
		fields: [
			{
				fieldname: "trans_items",
				fieldtype: "Table",
				label: __("Items"),
				cannot_add_rows: false,
				in_place_edit: false,
				reqd: 1,
				data: data,
				get_data: () => data,
				fields: fields,
			},
		],
		primary_action_label: __("Update"),
		primary_action: function () {
			const trans_items = this.get_values().trans_items.filter((r) => !!r.item_code);
			if (!trans_items.length) {
				frappe.msgprint(__("请至少保留一行明细"));
				return;
			}
			frappe.call({
				method: "cos.cos_stock.material_request_order_change.update_material_request_items",
				freeze: true,
				args: {
					mr_name: frm.doc.name,
					trans_items: JSON.stringify(trans_items),
				},
				callback: (r) => {
					if (!r.exc) {
						frm.reload_doc();
						this.hide();
					}
				},
			});
		},
	});

	dialog.show();
};

// Copyright (c) 2026, COS and contributors
// License: MIT. See license.txt

frappe.provide("cos.utils");

frappe.ui.form.on("Sales Order", {
	refresh: function (frm) {
		if (!frm.doc.name || frm.doc.__islocal) return;
		if (frm.doc.docstatus !== 1) return;
		if (frm.doc.status === "Closed") return;
		if (flt(frm.doc.per_delivered) >= 100 || flt(frm.doc.per_billed) >= 100) return;
		if (!frm.has_perm("write")) return;
		if (frm.doc.is_subcontracted) return;

		frm.add_custom_button(__("Update Taxes"), () => {
			cos.utils.update_sales_order_taxes_dialog(frm);
		});
	},
});

cos.utils.update_sales_order_taxes_dialog = function (frm) {
	const get_query = function () {
		return { filters: { company: frm.doc.company } };
	};

	const dialog = new frappe.ui.Dialog({
		title: __("Update Taxes"),
		fields: [
			{
				fieldtype: "Link",
				fieldname: "taxes_and_charges",
				label: __("Taxes and Charges Template"),
				options: "Sales Taxes and Charges Template",
				default: frm.doc.taxes_and_charges || "",
				get_query: get_query,
			},
			{
				fieldtype: "Link",
				fieldname: "tax_category",
				label: __("Tax Category"),
				options: "Tax Category",
				default: frm.doc.tax_category || "",
			},
		],
		primary_action_label: __("Update"),
		primary_action: function () {
			const values = this.get_values();
			frappe.call({
				method: "cos.cos_accounts.sales_order_tax_update.update_sales_order_taxes",
				freeze: true,
				args: {
					so_name: frm.doc.name,
					taxes_and_charges: values.taxes_and_charges || "",
					tax_category: values.tax_category || "",
				},
				callback: function (r) {
					if (!r.exc) {
						frm.reload_doc();
						dialog.hide();
					}
				},
			});
		},
	});

	dialog.show();
};

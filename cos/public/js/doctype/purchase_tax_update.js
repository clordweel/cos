// Copyright (c) 2026, COS and contributors
// License: MIT. See license.txt

frappe.provide("cos.utils");

function add_tax_update_button(frm, doctype) {
	if (!frm.doc.name || frm.doc.__islocal) return;
	if (frm.doc.docstatus !== 1) return;
	if (!frm.has_perm("write")) return;

	if (doctype === "Purchase Order") {
		if (frm.doc.status === "Closed") return;
		if (flt(frm.doc.per_received) >= 100) return;
		if (frm.doc.is_subcontracted) return;
	}
	if (doctype === "Purchase Receipt") {
		if (flt(frm.doc.per_billed) > 0) return;
	}

	frm.add_custom_button(__("税费变更"), () => {
		cos.utils.show_purchase_tax_update_dialog(frm, doctype);
	});
}

cos.utils.show_purchase_tax_update_dialog = function (frm, doctype) {
	const get_query = () => ({ filters: { company: frm.doc.company } });

	const fields = [
		{
			fieldtype: "Link",
			fieldname: "taxes_and_charges",
			label: __("Taxes and Charges Template"),
			options: "Purchase Taxes and Charges Template",
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
	];

	const dialog = new frappe.ui.Dialog({
		title: __("税费变更"),
		fields: fields,
		primary_action_label: __("Update"),
		primary_action: function () {
			const values = this.get_values();
			frappe.call({
				method: "cos.cos_accounts.purchase_tax_update.update_purchase_taxes",
				freeze: true,
				args: {
					doctype: doctype,
					docname: frm.doc.name,
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

frappe.ui.form.on("Purchase Order", {
	refresh: function (frm) {
		add_tax_update_button(frm, "Purchase Order");
	},
});

frappe.ui.form.on("Supplier Quotation", {
	refresh: function (frm) {
		add_tax_update_button(frm, "Supplier Quotation");
	},
});

frappe.ui.form.on("Purchase Receipt", {
	refresh: function (frm) {
		add_tax_update_button(frm, "Purchase Receipt");
	},
});

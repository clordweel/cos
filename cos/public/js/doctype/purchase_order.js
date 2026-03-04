// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh: function (frm) {
		if (!frm.doc.name || frm.doc.__islocal) return;
		frm.add_custom_button(__("添加运单"), function () {
			frappe.new_doc("Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
		frm.add_custom_button(__("查看运单列表"), function () {
			frappe.set_route("List", "Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
	},
});

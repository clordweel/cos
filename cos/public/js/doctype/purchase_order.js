// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh: function (frm) {
		// 隐藏物流信息 Tab（已迁移到独立 Order Shipment 单据）
		const hide_logistics_tab = () => {
			$(".form-layout .nav-link, .form-layout .page-link").each(function () {
				if ($(this).text().trim().indexOf("物流信息") >= 0) {
					$(this).closest(".nav-item, .page-item").hide();
				}
			});
		};
		hide_logistics_tab();
		setTimeout(hide_logistics_tab, 100);

		if (!frm.doc.name || frm.doc.__islocal) return;
		frm.add_custom_button(__("添加运单"), function () {
			frappe.new_doc("Order Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
		frm.add_custom_button(__("查看运单列表"), function () {
			frappe.set_route("List", "Order Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
	},
});

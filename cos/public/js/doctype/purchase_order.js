// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh: function (frm) {
		// 垫付员工：强制使用自定义查询以忽略 User Permission，采购经理可选取任意员工
		frm.set_query("custom_advance_employee", function () {
			return { query: "cos.cos_accounts.queries.advance_employee_query" };
		});
		if (!frm.doc.name || frm.doc.__islocal) return;
		frm.add_custom_button(__("添加运单"), function () {
			frappe.new_doc("Order Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
		frm.add_custom_button(__("查看运单列表"), function () {
			frappe.set_route("List", "Order Shipment", { purchase_order: frm.doc.name });
		}, __("物流运单"));
	},
	custom_is_employee_advance: function (frm) {
		// 勾选员工垫付且垫付员工为空时，默认填充当前登录用户的员工
		if (frm.doc.custom_is_employee_advance && !frm.doc.custom_advance_employee && frappe.boot.user?.employee) {
			frm.set_value("custom_advance_employee", frappe.boot.user.employee);
		}
	},
});

// 物料明细：选择物料后，从 Item 主采购链接即时带出采购平台、SKU、链接
frappe.ui.form.on("Purchase Order Item", "item_code", function (frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row.item_code || row.custom_platform) return; // 已选平台则不覆盖
	frappe.call({
		method: "cos.cos_buying.purchase_order_ecommerce.get_primary_purchase_source",
		args: { item_code: row.item_code },
		callback: function (r) {
			if (r.message) {
				frappe.model.set_value(cdt, cdn, "custom_platform", r.message.platform || "");
				frappe.model.set_value(cdt, cdn, "custom_platform_sku", r.message.platform_sku || "");
				frappe.model.set_value(cdt, cdn, "custom_purchase_url", r.message.purchase_url || "");
			}
		},
	});
});

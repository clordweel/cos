// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.listview_settings["Order Shipment"] = {
	add_fields: ["status"],
	get_indicator: function (doc) {
		const status_colors = {
			待确认: "gray",
			已发货: "blue",
			配送中: "orange",
			已签收: "green",
			异常: "red",
			已退回: "grey",
		};
		const color = status_colors[doc.status] || "gray";
		return [__(doc.status || "待确认"), color, "status,=," + (doc.status || "待确认")];
	},
};

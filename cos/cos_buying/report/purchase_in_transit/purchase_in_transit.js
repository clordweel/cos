// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase In Transit"] = {
	filters: [
		{
			fieldname: "order_type",
			label: __("订单类型"),
			fieldtype: "Select",
			options: "\n采购订单",
			default: "采购订单",
		},
		{
			fieldname: "company",
			label: __("公司"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "logistics_status",
			label: __("物流状态"),
			fieldtype: "Select",
			options: "\n全部\n在途\n已签收",
			default: "在途",
		},
		{
			fieldname: "supplier",
			label: __("供应商"),
			fieldtype: "Link",
			options: "Supplier",
		},
	],
};

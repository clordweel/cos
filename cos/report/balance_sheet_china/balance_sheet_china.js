// Copyright (c) 2025, cos and contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Balance Sheet China"] = $.extend({}, erpnext.financial_statements);

frappe.query_reports["Balance Sheet China"]["filters"].push(
	{
		fieldname: "accumulated_values",
		label: __("Accumulated Values"),
		fieldtype: "Check",
		default: 1,
	},
	{
		fieldname: "include_default_book_entries",
		label: __("Include Default FB Entries"),
		fieldtype: "Check",
		default: 1,
	},
	{
		fieldname: "selected_view",
		label: __("Select View"),
		fieldtype: "Select",
		options: [
			{ value: "Report", label: __("Report View") },
			{ value: "Growth", label: __("Growth View") },
		],
		default: "Report",
		reqd: 1,
	},
	{
		fieldname: "show_zero_values",
		label: __("Show zero values"),
		fieldtype: "Check",
	}
);

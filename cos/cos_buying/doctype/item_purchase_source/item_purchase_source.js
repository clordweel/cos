// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Purchase Source", {
	is_primary: function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.is_primary) return;
		// 确保仅一个主采购：取消同父表其他行的 is_primary
		const parentfield = row.parentfield || "custom_purchase_sources";
		const table = frm.doc[parentfield] || [];
		table.forEach((r) => {
			if (r.name !== cdn && r.is_primary) {
				frappe.model.set_value(cdt, r.name, "is_primary", 0);
			}
		});
	},
});

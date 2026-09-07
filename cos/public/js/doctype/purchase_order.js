// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

function _apply_advance_employee_readonly(frm) {
	if (frm.is_new() || frm.doc.docstatus !== 1) return;
	frappe.db.get_single_value("Buying Settings", "custom_advance_employee_editable_role").then((role) => {
		const user_roles = (frappe.user_roles || []).map((r) => r.toLowerCase());
		const allowed = role && user_roles.includes(role.toLowerCase());
		if (!allowed) {
			frm.set_df_property("custom_is_employee_advance", "read_only", 1);
			frm.set_df_property("custom_advance_employee", "read_only", 1);
		}
	});
}

function _po_payable_total(frm) {
	if (!cint(frm.doc.disable_rounded_total) && flt(frm.doc.rounded_total)) {
		return flt(frm.doc.rounded_total);
	}
	return flt(frm.doc.grand_total);
}

function _po_is_fully_paid(frm) {
	const total = _po_payable_total(frm);
	if (total <= 0) return false;
	return flt(frm.doc.advance_paid) >= total;
}

function _can_edit_po_item_rates(frm) {
	if (!frm.doc.name || frm.doc.__islocal) return false;
	if (frm.doc.docstatus !== 1) return false;
	if (!frm.has_perm("write")) return false;
	if (["Closed", "Cancelled"].includes(frm.doc.status)) return false;
	if (_po_is_fully_paid(frm)) return false;
	return true;
}

function _show_update_po_item_rates_dialog(frm) {
	const child_meta = frappe.get_meta("Purchase Order Item");
	const rate_field = (child_meta.fields || []).find((f) => f.fieldname === "rate");
	const rate_fieldtype = rate_field && rate_field.fieldtype === "Float" ? "Float" : "Currency";
	const get_precision = (fieldname) => {
		const df = (child_meta.fields || []).find((f) => f.fieldname === fieldname);
		return df ? df.precision : undefined;
	};

	const data = (frm.doc.items || []).map((d) => ({
		docname: d.name,
		item_code: d.item_code,
		item_name: d.item_name,
		qty: d.qty,
		uom: d.uom,
		rate: d.rate,
		schedule_date: d.schedule_date,
		conversion_factor: d.conversion_factor,
		description: d.description,
	}));

	const dialog = new frappe.ui.Dialog({
		title: __("修改单价"),
		size: "extra-large",
		fields: [
			{
				fieldname: "trans_items",
				fieldtype: "Table",
				label: __("Items"),
				cannot_add_rows: true,
				cannot_delete_rows: true,
				in_place_edit: false,
				reqd: 1,
				data: data,
				get_data: () => data,
				fields: [
					{ fieldtype: "Data", fieldname: "docname", read_only: 1, hidden: 1 },
					{
						fieldtype: "Link",
						fieldname: "item_code",
						options: "Item",
						label: __("Item Code"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldtype: "Data",
						fieldname: "item_name",
						label: __("Item Name"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldtype: "Float",
						fieldname: "qty",
						label: __("Qty"),
						in_list_view: 1,
						read_only: 1,
						precision: get_precision("qty"),
					},
					{
						fieldtype: "Data",
						fieldname: "uom",
						label: __("UOM"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldtype: rate_fieldtype,
						fieldname: "rate",
						options: rate_fieldtype === "Currency" ? "currency" : undefined,
						label: __("Rate"),
						in_list_view: 1,
						read_only: 0,
						reqd: 1,
						precision: get_precision("rate"),
					},
				],
			},
		],
		primary_action_label: __("Update"),
		primary_action: function () {
			const trans_items = this.get_values()["trans_items"].filter((item) => !!item.item_code);
			frappe.call({
				method: "erpnext.controllers.accounts_controller.update_child_qty_rate",
				freeze: true,
				args: {
					parent_doctype: frm.doc.doctype,
					trans_items: trans_items,
					parent_doctype_name: frm.doc.name,
					child_docname: "items",
				},
				callback: function (r) {
					if (!r.exc) {
						frm.reload_doc();
					}
				},
			});
			this.hide();
		},
	});
	dialog.show();
}

frappe.ui.form.on("Purchase Order", {
	refresh: function (frm) {
		// 垫付员工：强制使用自定义查询以忽略 User Permission，采购经理可选取任意员工
		frm.set_query("custom_advance_employee", function () {
			return { query: "cos.cos_accounts.queries.advance_employee_query" };
		});
		_apply_advance_employee_readonly(frm);
		if (_can_edit_po_item_rates(frm)) {
			frm.add_custom_button(__("修改单价"), function () {
				_show_update_po_item_rates_dialog(frm);
			});
		}
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
	custom_shipping_contact_person: function (frm) {
		const link = frm.doc.custom_shipping_contact_person;
		if (!link) {
			frm.set_value("custom_shipping_contact_phone", "");
			return;
		}
		frappe.db.get_value("Contact", link, ["phone", "mobile_no"]).then((r) => {
			const msg = r.message || {};
			frm.set_value("custom_shipping_contact_phone", (msg.phone || msg.mobile_no || "").trim());
		});
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

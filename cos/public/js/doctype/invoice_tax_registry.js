// Copyright (c) 2026, bit and contributors
// For license information, please see license.txt

function add_create_tax_registry_button(frm) {
	// 仅对已提交发票显示
	if (frm.is_new() || frm.doc.docstatus !== 1) return;

	frm.add_custom_button(
		__("税务登记"),
		() => create_tax_registry_from_invoice(frm),
		__("Create")
	);
}

async function create_tax_registry_from_invoice(frm) {
	// 若发票已被税务登记引用，则直接提示并打开引用单据（不干预发票流程）
	if (frm.doc.custom_tax_registry_reference) {
		const ref = frm.doc.custom_tax_registry_reference;
		frappe.msgprint({
			title: __("已存在税务登记"),
			message: __(
				"该发票已被税务登记单 {0} 引用。",
				[frappe.utils.get_form_link("Tax Registry", ref, true)]
			),
		});
		return;
	}

	// 创建 Tax Registry 新单，并预填父表/子表
	await frappe.model.with_doctype("Tax Registry");
	const tr = frappe.model.get_new_doc("Tax Registry");

	// 父表预填
	tr.invoice_doctype = frm.doctype;
	tr.company = frm.doc.company;
	// 不使用发票单据编号自动填充发票号（留空由用户填写）
	tr.posting_date = frm.doc.posting_date || frappe.datetime.get_today();
	tr.posting_time = frm.doc.posting_time || frappe.datetime.now_time();

	// 子表新增一行
	const row = frappe.model.add_child(tr, "Tax Registry Item", "tax_registry_item");
	row.invoice_doctype = frm.doctype;
	row.invoice = frm.doc.name;
	row.posting_date = frm.doc.posting_date || null;
	row.grand_total = frm.doc.grand_total || 0;
	row.total_taxes_and_charges = frm.doc.total_taxes_and_charges || 0;

	// customer / supplier
	if (frm.doctype === "Sales Invoice") {
		row.customer = frm.doc.customer || "";
		row.supplier = "";
	} else if (frm.doctype === "Purchase Invoice") {
		row.supplier = frm.doc.supplier || "";
		row.customer = "";
	}

	// tax_id（尽量带出；不阻塞创建）
	try {
		const party_doctype = frm.doctype === "Sales Invoice" ? "Customer" : "Supplier";
		const party_name = frm.doctype === "Sales Invoice" ? frm.doc.customer : frm.doc.supplier;
		if (party_name) {
			const r = await frappe.db.get_value(party_doctype, party_name, "tax_id");
			row.tax_id = (r && r.message && r.message.tax_id) || "";
		}
	} catch (e) {
		// ignore
	}

	// 跳转到新建的 Tax Registry
	frappe.set_route("Form", "Tax Registry", tr.name);
}

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		add_create_tax_registry_button(frm);
	},
});

frappe.ui.form.on("Purchase Invoice", {
	refresh(frm) {
		add_create_tax_registry_button(frm);
		add_create_payable_transfer_je_button(frm);
		add_create_employee_advance_payment_button(frm);
	},
});

function add_create_payable_transfer_je_button(frm) {
	if (frm.doc.doctype !== "Purchase Invoice" || frm.is_new() || frm.doc.docstatus !== 1) return;
	if (!frm.doc.custom_is_employee_advance || !frm.doc.custom_advance_employee) return;
	if (frm.doc.custom_payable_transfer_je) return;

	frm.add_custom_button(
		__("应付转员工"),
		() => create_payable_transfer_je_from_pi(frm),
		__("Create")
	);
}

async function create_payable_transfer_je_from_pi(frm) {
	try {
		const r = await frappe.call({
			method: "cos.cos_accounts.utils.employee_advance_payable_transfer.create_payable_transfer_je",
			args: { docname: frm.doc.name },
			freeze: true,
		});
		if (r.message && r.message.journal_entry) {
			frappe.show_alert({
				message: __("已创建应付转员工日记账：{0}", [
					frappe.utils.get_form_link("Journal Entry", r.message.journal_entry, true),
				]),
				indicator: "green",
			}, 5);
			frm.reload_doc();
		}
	} catch (e) {
		// frappe.call already shows error
	}
}

function add_create_employee_advance_payment_button(frm) {
	if (frm.doc.doctype !== "Purchase Invoice" || frm.is_new() || frm.doc.docstatus !== 1) return;
	if (!frm.doc.custom_is_employee_advance || !frm.doc.custom_advance_employee) return;
	if (!frm.doc.custom_payable_transfer_je) return;

	frm.add_custom_button(
		__("付给员工"),
		() => create_employee_advance_payment_from_pi(frm),
		__("Create")
	);
}

async function create_employee_advance_payment_from_pi(frm) {
	try {
		const r = await frappe.call({
			method: "cos.cos_accounts.utils.employee_advance_payable_transfer.create_employee_advance_payment",
			args: { docname: frm.doc.name },
			freeze: true,
		});
		if (r.message && r.message.payment_entry) {
			frappe.show_alert({
				message: __("已创建付款条目：{0}，请核对后提交", [
					frappe.utils.get_form_link("Payment Entry", r.message.payment_entry, true),
				]),
				indicator: "green",
			}, 5);
			frappe.set_route("Form", "Payment Entry", r.message.payment_entry);
		}
	} catch (e) {
		// frappe.call already shows error
	}
}


// Copyright (c) 2026, bit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tax Registry", {
	refresh(frm) {
		// 记录上一次 invoice_doctype，用于判断是否“切换”而非首次赋值
		if (typeof frm._last_invoice_doctype === "undefined") {
			frm._last_invoice_doctype = frm.doc.invoice_doctype || null;
		}
		// 取消单据时不联动取消发票（避免影响系统内置发票管理）
		// 该变量会被 Frappe 用于 cancel-with-children 的预检查与联动取消逻辑
		frm.ignore_doctypes_on_cancel_all = ["Sales Invoice", "Purchase Invoice"];

		// 新建文档时，自动填充 posting_date 和 posting_time
		if (frm.is_new()) {
			if (!frm.doc.posting_date) {
				frm.set_value("posting_date", frappe.datetime.get_today());
			}
			if (!frm.doc.posting_time) {
				frm.set_value("posting_time", frappe.datetime.now_time());
			}
		}
		// 确保子表的 invoice_doctype 与父表保持一致
		update_child_table_invoice_doctype(frm);
		// 约束子表 invoice 筛选：公司=父表 company，未被其它税务登记引用，状态排除草稿/退货/贷项/取消/内部调拨，并排除已添加行中的发票
		frm.set_query("invoice", "tax_registry_item", function(txt, cdt, cdn) {
			let row = locals[cdt][cdn];
			if (!frm.doc.company || !row.invoice_doctype) return;
			let filters = {
				company: frm.doc.company,
				status: ["not in", [
					"Draft",
					"Return",
					"Credit Note Issued",
					"Cancelled",
					"Internal Transfer"
				]]
			};
			// 未被其它税务登记引用：允许为空或等于当前单据号（编辑已保存单据时允许回选）
			if (frm.doc.name) {
				filters.custom_tax_registry_reference = ["in", ["", frm.doc.name]];
			} else {
				// 新建未保存时仅允许空
				filters.custom_tax_registry_reference = ["in", [""]];
			}
			// 排除已在本子表其它行中选中的发票（同单据类型）
			let used = [];
			(frm.doc.tax_registry_item || []).forEach(function(r) {
				if (r.invoice_doctype === row.invoice_doctype && r.invoice && r !== row) {
					used.push(r.invoice);
				}
			});
			if (used.length) {
				filters.name = ["not in", used];
			}
			return { filters: filters };
		});
		// 合计子表发票金额/税额到父表 grand_total / total_taxes_and_charges
		update_parent_totals(frm);
		// 预览-会计凭据：复用 ERPNext 的 Accounting Ledger Preview（和采购发票草稿一致）
		if (window.erpnext?.accounts?.ledger_preview) {
			erpnext.accounts.ledger_preview.show_accounting_ledger_preview(frm);
		}
		// 提交后：查看-会计凭证（指向会计账本页面）
		if (!frm.is_new() && frm.doc.docstatus > 0) {
			frm.add_custom_button(
				__("会计凭证"),
				function() {
					frappe.route_options = {
						voucher_no: frm.doc.name,
						from_date: frm.doc.posting_date,
						to_date: frappe.datetime.get_today(),
						company: frm.doc.company,
						categorize_by: "Categorize by Voucher (Consolidated)",
						show_cancelled_entries: frm.doc.docstatus === 2,
						ignore_prepared_report: true
					};
					frappe.set_route("query-report", "General Ledger");
				},
				__("View")
			);
		}
	},

	invoice_doctype(frm) {
		// 避免在脚本回滚字段时重复触发
		if (frm._ignore_invoice_doctype_change) {
			frm._ignore_invoice_doctype_change = false;
			frm._last_invoice_doctype = frm.doc.invoice_doctype || null;
			update_child_table_invoice_doctype(frm);
			update_accounts_from_company(frm);
			return;
		}

		const new_value = frm.doc.invoice_doctype || null;
		const old_value = typeof frm._last_invoice_doctype === "undefined" ? null : frm._last_invoice_doctype;

		// 首次赋值（旧值为空）不提示清空；仅在“切换”时提示
		const is_switching = !!old_value && new_value && old_value !== new_value;

		if (new_value) {
			// 检查子表是否不为空（仅在切换时提示）
			if (is_switching && frm.doc.tax_registry_item && frm.doc.tax_registry_item.length > 0) {
				frappe.confirm(
					__("子表不为空，是否清除子表数据？"),
					function () {
						// 用户确认清除
						frm.clear_table("tax_registry_item");
						frm.refresh_field("tax_registry_item");
						// 清空子表时，同步清空父表合计与总税费
						update_parent_totals(frm);
						frm._last_invoice_doctype = new_value;
						// 更新账户字段
						update_accounts_from_company(frm);
					},
					function () {
						// 用户取消：回滚 invoice_doctype 到旧值（避免子表与单据类型不一致）
						frm._ignore_invoice_doctype_change = true;
						frm.set_value("invoice_doctype", old_value);
						frm._last_invoice_doctype = old_value;
					}
				);
				return;
			}

			// 非切换或子表为空：直接同步子表 invoice_doctype
			update_child_table_invoice_doctype(frm);
			// 更新账户字段
			update_accounts_from_company(frm);
		}

		frm._last_invoice_doctype = new_value;
	},

	company(frm) {
		// 当公司改变时，更新账户字段
		if (frm.doc.invoice_doctype && frm.doc.company) {
			update_accounts_from_company(frm);
		}
	}
});

// 更新子表的 invoice_doctype 字段
function update_child_table_invoice_doctype(frm) {
	if (frm.doc.invoice_doctype && frm.doc.tax_registry_item) {
		frm.doc.tax_registry_item.forEach(function(row) {
			row.invoice_doctype = frm.doc.invoice_doctype;
		});
		frm.refresh_field("tax_registry_item");
	}
}

// 合计子表 grand_total / total_taxes_and_charges 到父表
function update_parent_totals(frm) {
	if (!frm.doc.tax_registry_item || !frm.doc.tax_registry_item.length) {
		frm.set_value("grand_total", 0);
		frm.set_value("total_taxes_and_charges", 0);
		return;
	}
	let grand_total = 0;
	let total_taxes_and_charges = 0;
	frm.doc.tax_registry_item.forEach(function(row) {
		grand_total += flt(row.grand_total, 2);
		total_taxes_and_charges += flt(row.total_taxes_and_charges, 2);
	});
	frm.set_value("grand_total", grand_total);
	frm.set_value("total_taxes_and_charges", total_taxes_and_charges);
}

// 根据 invoice_doctype 和 company 更新账户字段
function update_accounts_from_company(frm) {
	if (!frm.doc.invoice_doctype || !frm.doc.company) {
		return;
	}

	// 获取公司的自定义字段
	frappe.db.get_value("Company", frm.doc.company, [
		"custom_buying_tax_account",
		"custom_buying_tax_account_used",
		"custom_selling_tax_account",
		"custom_selling_tax_account_used"
	]).then(function(r) {
		if (!r.message) {
			return;
		}

		let company = r.message;
		let debit_account = null;
		let credit_account = null;

		if (frm.doc.invoice_doctype === "Sales Invoice") {
			// 销售发票：借方 = 销项税额-已开票，贷方 = 销项税额
			debit_account = company.custom_selling_tax_account_used;
			credit_account = company.custom_selling_tax_account;
		} else if (frm.doc.invoice_doctype === "Purchase Invoice") {
			// 采购发票：借方 = 进项税额，贷方 = 进项税额-已抵扣
			debit_account = company.custom_buying_tax_account;
			credit_account = company.custom_buying_tax_account_used;
		}

		// 更新账户字段
		if (debit_account) {
			frm.set_value("debit_account", debit_account);
		}
		if (credit_account) {
			frm.set_value("credit_account", credit_account);
		}
	}).catch(function(error) {
		console.error("获取公司信息失败:", error);
		frappe.msgprint(__("获取公司账户信息失败，请检查公司设置"));
	});
}

// 子表事件处理
frappe.ui.form.on("Tax Registry Item", {
	// 当添加新行时，自动设置 invoice_doctype
	tax_registry_item_add(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.doc.invoice_doctype) {
			row.invoice_doctype = frm.doc.invoice_doctype;
			frm.refresh_field("tax_registry_item");
		}
		update_parent_totals(frm);
	},

	// 当删除子表行时，重新合计父表 grand_total
	tax_registry_item_remove(frm) {
		update_parent_totals(frm);
	},

	// 当 invoice_doctype 字段改变时（虽然只读，但确保一致性）
	invoice_doctype(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.doc.invoice_doctype && row.invoice_doctype !== frm.doc.invoice_doctype) {
			row.invoice_doctype = frm.doc.invoice_doctype;
			// 如果 invoice_doctype 改变，清空 invoice 字段和相关数据
			row.invoice = "";
			row.grand_total = 0;
			row.total_taxes_and_charges = 0;
			row.posting_date = null;
			row.tax_id = "";
			row.customer = "";
			row.supplier = "";
			frm.refresh_field("tax_registry_item");
		}
		update_parent_totals(frm);
	},

	// 当选择发票时，自动带出相关数据
	invoice(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.invoice && row.invoice_doctype) {
			// 限制不允许重复添加同一发票
			if (is_duplicate_invoice(frm, cdt, cdn)) {
				row.invoice = "";
				row.grand_total = 0;
				row.total_taxes_and_charges = 0;
				row.posting_date = null;
				row.tax_id = "";
				row.customer = "";
				row.supplier = "";
				frm.refresh_field("tax_registry_item");
				update_parent_totals(frm);
				frappe.msgprint(__("该发票已在子表中添加，不可重复添加。"));
				return;
			}
			// 从发票中获取数据
			fetch_invoice_data(frm, row, cdt, cdn);
		} else {
			// 清空相关字段
			row.grand_total = 0;
			row.total_taxes_and_charges = 0;
			row.posting_date = null;
			row.tax_id = "";
			row.customer = "";
			row.supplier = "";
			frm.refresh_field("tax_registry_item");
			update_parent_totals(frm);
		}
	}
});

// 检查子表当前行所选发票是否与其它行重复（同一 invoice_doctype + invoice 只允许出现一次）
function is_duplicate_invoice(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (!row.invoice || !row.invoice_doctype) return false;
	let count = 0;
	(frm.doc.tax_registry_item || []).forEach(function(r) {
		if (r.invoice_doctype === row.invoice_doctype && r.invoice === row.invoice) {
			count++;
		}
	});
	return count > 1;
}

// 从发票中获取数据并填充到子表行
function fetch_invoice_data(frm, row, cdt, cdn) {
	if (!row.invoice || !row.invoice_doctype) {
		return;
	}

	// 确定要获取的字段
	let party_field = row.invoice_doctype === "Sales Invoice" ? "customer" : "supplier";
	let fields = ["grand_total", "total_taxes_and_charges", "posting_date", party_field];

	// 获取发票的基本信息（包括客户/供应商）
	frappe.db.get_value(row.invoice_doctype, row.invoice, fields)
		.then(function(invoice_r) {
			if (!invoice_r.message) {
				return;
			}

			let invoice = invoice_r.message;
			
			// 填充 grand_total、posting_date，以及根据单据类型填充 customer / supplier
			row.grand_total = invoice.grand_total || 0;
			row.total_taxes_and_charges = invoice.total_taxes_and_charges || 0;
			row.posting_date = invoice.posting_date || null;
			if (row.invoice_doctype === "Sales Invoice") {
				row.customer = invoice.customer || "";
				row.supplier = "";
			} else if (row.invoice_doctype === "Purchase Invoice") {
				row.supplier = invoice.supplier || "";
				row.customer = "";
			}

			// 获取税号：Sales Invoice 从 customer 获取，Purchase Invoice 从 supplier 获取
			if (invoice[party_field]) {
				let party_name = invoice[party_field];
				let party_doctype = row.invoice_doctype === "Sales Invoice" ? "Customer" : "Supplier";
				
				// 获取客户或供应商的税号
				frappe.db.get_value(party_doctype, party_name, "tax_id")
					.then(function(tax_r) {
						if (tax_r.message && tax_r.message.tax_id) {
							row.tax_id = tax_r.message.tax_id;
						} else {
							row.tax_id = "";
						}
						frm.refresh_field("tax_registry_item");
						update_parent_totals(frm);
					})
					.catch(function(error) {
						console.error("获取税号失败:", error);
						row.tax_id = "";
						frm.refresh_field("tax_registry_item");
						update_parent_totals(frm);
					});
			} else {
				row.tax_id = "";
				frm.refresh_field("tax_registry_item");
				update_parent_totals(frm);
			}
		})
		.catch(function(error) {
			console.error("获取发票信息失败:", error);
			frappe.msgprint(__("获取发票信息失败，请检查发票是否存在"));
		});
}

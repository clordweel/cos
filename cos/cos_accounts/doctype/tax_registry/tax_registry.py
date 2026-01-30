# Copyright (c) 2026, bit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt
from frappe.utils.data import get_link_to_form


class TaxRegistry(Document):
	def validate(self):
		self._set_totals_from_children()
		self._validate_no_duplicate_invoice()
		self._validate_child_invoices()

	def before_submit(self):
		# invoice_number 取消 Unique 后，提交时仍需保证唯一（排除已取消记录）
		self._validate_invoice_number_unique_on_submit()

	def before_cancel(self):
		"""取消前尽量不被外部单据链接阻拦。

		发票侧存在 custom_tax_registry_reference 指向本单据时，Frappe 默认会阻止取消并弹出
		“取消所有关联单据？”的提示。税务登记不应干预发票流程，因此这里跳过链接校验，
		并在 on_cancel 中清空发票引用字段。
		"""
		self.flags.ignore_links = True
		# 仅用于 Cancel 链接校验的忽略列表（Delete 不使用该列表）
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry", "Sales Invoice", "Purchase Invoice"]

	def make_gl_entries(self):
		"""用于“会计账本预览（Accounting Ledger Preview）”生成 GL 分录（预览会 rollback，不会实际过账）。"""
		self.make_gl_entries_internal(cancel=False)

	def on_submit(self):
		# 1) 过账（生成 GL Entries）
		self.make_gl_entries_internal(cancel=False)
		# 2) 写入税务登记引用（发票上记录税务登记单号）
		self._set_invoices_tax_registry_reference(self.name)

	def on_cancel(self):
		# 取消时允许存在 GL Entry / Payment Ledger Entry 的动态链接（否则会被链接校验拦截）
		# 参考 ERPNext: Process Deferred Accounting / POS Invoice 的做法
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry", "Sales Invoice", "Purchase Invoice"]
		self.flags.ignore_links = True
		# 1) 冲销 GL Entries
		self.make_gl_entries_internal(cancel=True)
		# 2) 清空税务登记引用（双保险：子表逐行 + 反查字段等于本单据号的发票）
		self._set_invoices_tax_registry_reference(None)
		self._clear_invoices_referencing_self()

	def on_trash(self):
		"""删除前清理本单据生成的内部凭证（GL/Payment Ledger），避免被链接校验拦截。

		注意：Frappe 的 delete 流程是先执行 on_trash，再做链接检查。
		"""
		# 草稿允许直接删除；已提交单据不允许删除（需先取消）；已取消单据允许删除
		if self.docstatus == 1:
			frappe.throw(_("请先取消该税务登记单再删除。"))

		# 若启用不可变账本：仅当本单据确实生成过 GL Entry 时，才禁止删除
		try:
			gl_exists = bool(
				frappe.db.exists("GL Entry", {"voucher_type": self.doctype, "voucher_no": self.name})
			)
			if gl_exists:
				from erpnext.accounts.utils import is_immutable_ledger_enabled

				if is_immutable_ledger_enabled():
					frappe.throw(_("已启用不可变账本，禁止删除包含会计分录的单据。"))
		except Exception:
			# erpnext 不可用时忽略（一般不会发生）
			pass

		# 清理关联的 GL Entry / Payment Ledger Entry（若存在）
		frappe.db.delete("GL Entry", {"voucher_type": self.doctype, "voucher_no": self.name})
		frappe.db.delete("Payment Ledger Entry", {"voucher_type": self.doctype, "voucher_no": self.name})
		frappe.db.delete(
			"Advance Payment Ledger Entry", {"voucher_type": self.doctype, "voucher_no": self.name}
		)
		# 同时清空发票上的税务登记引用（仅清空引用等于本单据号的发票）
		self._set_invoices_tax_registry_reference(None)
		self._clear_invoices_referencing_self()

	def make_gl_entries_internal(self, cancel: bool = False):
		"""创建/冲销 GL Entries。cancel=True 时做反向分录。"""
		if cancel:
			# 取消：基于已生成的 GL Entry 做冲销（更符合 ERPNext 标准流程）
			from erpnext.accounts.general_ledger import make_gl_entries

			gl_entries = frappe.get_all(
				"GL Entry",
				fields=["*"],
				filters={"voucher_type": self.doctype, "voucher_no": self.name, "is_cancelled": 0},
			)
			if gl_entries:
				make_gl_entries(gl_map=gl_entries, cancel=True)
			return

		if not (self.company and self.posting_date and self.debit_account and self.credit_account):
			return

		# 税务登记对应税科目分录：金额使用 total_taxes_and_charges
		amount = flt(self.total_taxes_and_charges, 2)
		if not amount:
			return

		cost_center = frappe.get_cached_value("Company", self.company, "cost_center")

		gl_map = [
			frappe._dict(
				{
					"posting_date": self.posting_date,
					"company": self.company,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"remarks": _("Tax Registry {0}").format(self.name),
					"account": self.debit_account,
					"against": self.credit_account,
					"debit": amount,
					"credit": 0,
					"debit_in_account_currency": amount,
					"credit_in_account_currency": 0,
					"cost_center": cost_center,
				}
			),
			frappe._dict(
				{
					"posting_date": self.posting_date,
					"company": self.company,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"remarks": _("Tax Registry {0}").format(self.name),
					"account": self.credit_account,
					"against": self.debit_account,
					"debit": 0,
					"credit": amount,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": amount,
					"cost_center": cost_center,
				}
			),
		]

		from erpnext.accounts.general_ledger import make_gl_entries

		make_gl_entries(gl_map, cancel=False, merge_entries=False)

	def _set_totals_from_children(self):
		"""服务端汇总子表金额，保证提交/过账使用的金额一致。"""
		grand_total = 0
		total_taxes_and_charges = 0
		for d in self.tax_registry_item or []:
			grand_total += flt(getattr(d, "grand_total", 0), 2)
			total_taxes_and_charges += flt(getattr(d, "total_taxes_and_charges", 0), 2)
		self.grand_total = grand_total
		self.total_taxes_and_charges = total_taxes_and_charges

	def _set_invoices_tax_registry_reference(self, reference: str | None):
		"""写入/清空发票上的税务登记引用字段 custom_tax_registry_reference。

		- reference 为字符串时：写入该税务登记单号
		- reference 为 None 时：仅当发票当前引用等于本单据号时才清空，避免误清其它单据的引用
		"""
		for item in self.tax_registry_item or []:
			if not item.invoice_doctype or not item.invoice:
				continue

			if reference is None:
				current = frappe.db.get_value(
					item.invoice_doctype, item.invoice, "custom_tax_registry_reference"
				)
				if current and current != self.name:
					continue
				value = ""
			else:
				value = reference

			frappe.db.set_value(
				item.invoice_doctype,
				item.invoice,
				"custom_tax_registry_reference",
				value,
				update_modified=False,
			)

	def _clear_invoices_referencing_self(self):
		"""兜底清理：将所有 custom_tax_registry_reference == 本单据号 的发票清空。

		用于防止子表行不完整/被外部改动导致的遗漏。
		"""
		for dt in ("Sales Invoice", "Purchase Invoice"):
			for inv in frappe.get_all(
				dt,
				filters={"custom_tax_registry_reference": self.name},
				pluck="name",
			):
				frappe.db.set_value(
					dt,
					inv,
					"custom_tax_registry_reference",
					"",
					update_modified=False,
				)

	def _validate_child_invoices(self):
		"""服务端兜底校验：子表发票类型/公司必须与父表一致，且不得被其它税务登记引用。"""
		if not self.invoice_doctype or not self.company:
			return

		for item in self.tax_registry_item or []:
			if item.invoice_doctype and item.invoice_doctype != self.invoice_doctype:
				frappe.throw(
					_("子表发票类型必须与父表 Invoice Doctype 一致。"),
					title=_("发票类型不一致"),
				)
			if item.invoice:
				inv_company = frappe.db.get_value(item.invoice_doctype, item.invoice, "company")
				if inv_company and inv_company != self.company:
					frappe.throw(
						_("子表发票所属公司必须与父表 Company 一致：{0}").format(item.invoice),
						title=_("公司不一致"),
					)
				# 不允许选择已被其它税务登记引用的发票
				ref = frappe.db.get_value(
					item.invoice_doctype, item.invoice, "custom_tax_registry_reference"
				)
				if ref and ref != self.name:
					frappe.throw(
						_("发票 {0} 已被税务登记单 {1} 引用，无法重复引用。").format(item.invoice, ref),
						title=_("发票已被引用"),
					)

	def _validate_no_duplicate_invoice(self):
		"""子表不允许重复添加同一发票（同一 invoice_doctype + invoice 只允许出现一次）"""
		seen = set()
		for item in self.tax_registry_item or []:
			if not item.invoice_doctype or not item.invoice:
				continue
			key = (item.invoice_doctype, item.invoice)
			if key in seen:
				frappe.throw(
					frappe._("子表中存在重复发票：{0} - {1}，请勿重复添加。").format(
						item.invoice_doctype, item.invoice
					),
					title=frappe._("重复发票"),
				)
			seen.add(key)

	def _validate_invoice_number_unique_on_submit(self):
		if not self.invoice_number:
			return

		existing = frappe.db.get_value(
			"Tax Registry",
			{
				"invoice_number": self.invoice_number,
				"name": ("!=", self.name),
				"docstatus": ("<", 2),  # 排除已取消
			},
			"name",
		)
		if existing:
			existing_link = get_link_to_form("Tax Registry", existing, existing)
			frappe.throw(
				_("发票号 {0} 已被税务登记单 {1} 使用，无法重复提交。").format(
					frappe.bold(self.invoice_number), existing_link
				),
				title=_("发票号重复"),
			)

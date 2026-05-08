# Copyright (c) 2026, COS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeAdvancePIReimbursement(Document):
	def validate(self):
		from cos.cos_accounts.utils.employee_advance_pi_reimbursement_workflow import (
			eapr_validate_duplicate_and_pi,
		)

		eapr_validate_duplicate_and_pi(self)

	def on_submit(self):
		from cos.cos_accounts.utils import employee_advance_payable_transfer

		if frappe.flags.in_install or frappe.flags.in_migrate:
			return

		user = self.get("custom_eapr_director_approved_by") or frappe.session.user
		now = frappe.utils.now()
		frappe.db.set_value(
			"Purchase Invoice",
			self.purchase_invoice,
			{
				"custom_reimbursement_approval_status": "Approved",
				"custom_reimbursement_approved_by": user,
				"custom_reimbursement_approved_on": now,
				"custom_reimbursement_remark": ((self.remark or "")[:140] if self.remark else None),
			},
			update_modified=True,
		)

		employee_advance_payable_transfer.create_payable_transfer_je(self.purchase_invoice)

	def on_cancel(self):
		pi_name = self.purchase_invoice
		if not pi_name:
			return

		has_je = frappe.db.get_value("Purchase Invoice", pi_name, "custom_payable_transfer_je")
		if has_je:
			frappe.throw(
				_("关联采购发票已存在应付转员工日记账 {0}，请先取消日记账后再取消报销单").format(has_je),
				title=_("无法取消"),
			)

		frappe.db.set_value(
			"Purchase Invoice",
			pi_name,
			{
				"custom_reimbursement_approval_status": "Pending",
				"custom_reimbursement_approved_by": None,
				"custom_reimbursement_approved_on": None,
				"custom_reimbursement_remark": None,
			},
			update_modified=True,
		)

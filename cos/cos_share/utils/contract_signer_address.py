# Copyright (c) 2026, COS and contributors
"""采购/销售订单：签订代表「通讯地址」为 Link(Address)，从联系人 primary address 或 Dynamic Link 带出。"""

from __future__ import annotations

import frappe


def _address_name_for_contact(contact_name: str | None) -> str | None:
	if not contact_name:
		return None
	addr = frappe.db.get_value("Contact", contact_name, "address")
	if addr:
		return addr
	rows = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Address",
			"link_doctype": "Contact",
			"link_name": contact_name,
		},
		pluck="parent",
		limit=1,
	)
	return rows[0] if rows else None


def sync_contract_signer_addresses(doc, method=None):
	"""validate：签订代表变更或地址为空时，写入联系人关联的 Address 单号（与 fetch_from 互补，覆盖仅 Dynamic Link 有地址的情况）。"""
	if doc.doctype not in ("Purchase Order", "Sales Order"):
		return

	prev = doc.get_doc_before_save() if not doc.is_new() else None
	pairs = (
		("custom_first_party_signer", "custom_first_party_signer_address"),
		("custom_second_party_signer", "custom_second_party_signer_address"),
	)

	for signer_field, addr_field in pairs:
		signer = doc.get(signer_field)
		prev_signer = prev.get(signer_field) if prev else None

		if not signer:
			doc.set(addr_field, "")
			continue

		addr_name = _address_name_for_contact(signer)
		current = doc.get(addr_field)

		if signer != prev_signer:
			doc.set(addr_field, addr_name or "")
		elif not current:
			doc.set(addr_field, addr_name or "")

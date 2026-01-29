import frappe
from frappe import _


def _get_linked_tax_registries(invoice_doctype: str, invoice_name: str) -> list[str]:
	"""返回引用该发票的 Tax Registry 列表（去重）。"""
	refs: set[str] = set()

	# 1) 优先用发票上的引用字段（若存在）
	ref = frappe.db.get_value(invoice_doctype, invoice_name, "custom_tax_registry_reference")
	if ref:
		refs.add(ref)

	# 2) 兜底：从子表 Tax Registry Item 反查 parent
	for row in frappe.get_all(
		"Tax Registry Item",
		filters={
			"parenttype": "Tax Registry",
			"invoice_doctype": invoice_doctype,
			"invoice": invoice_name,
		},
		fields=["parent"],
	):
		if row.parent:
			refs.add(row.parent)

	return list(refs)


def _unlink_invoice_from_draft_tax_registry(tax_registry_name: str, invoice_doctype: str, invoice_name: str):
	"""从草稿 Tax Registry 中移除引用该发票的行。"""
	tr = frappe.get_doc("Tax Registry", tax_registry_name)
	if tr.docstatus != 0:
		return

	original_len = len(tr.tax_registry_item or [])
	tr.tax_registry_item = [
		d
		for d in (tr.tax_registry_item or [])
		if not (d.invoice_doctype == invoice_doctype and d.invoice == invoice_name)
	]
	if len(tr.tax_registry_item) == original_len:
		return

	tr.flags.ignore_permissions = True
	tr.save()


def invoice_before_cancel(doc, method=None):
	"""取消发票前：不取消任何关联单据，仅清空发票上的税务登记引用字段，并忽略 Tax Registry 的动态链接校验。"""
	# 让发票取消时不被 Tax Registry Item 的动态链接拦截
	doc.ignore_linked_doctypes = (doc.get("ignore_linked_doctypes") or []) + ["Tax Registry"]
	# 更进一步：本次取消不做任何反向链接检查（避免税务登记干扰发票内置取消流程）
	doc.flags.ignore_links = True

	# 清空发票上的税务登记引用字段（不触发发票 cancel / 不修改税务登记）
	frappe.db.set_value(
		doc.doctype,
		doc.name,
		"custom_tax_registry_reference",
		"",
		update_modified=False,
	)


def invoice_on_trash(doc, method=None):
	"""删除发票前：不干预系统内置删除逻辑，仅尽力清空引用字段。

	说明：删除（Delete）时 Frappe 的动态链接校验不支持 per-doc ignore_linked_doctypes，
	是否允许删除仍由系统链接校验决定；这里不再阻止/联动处理任何 Tax Registry。
	"""
	frappe.db.set_value(
		doc.doctype,
		doc.name,
		"custom_tax_registry_reference",
		"",
		update_modified=False,
	)


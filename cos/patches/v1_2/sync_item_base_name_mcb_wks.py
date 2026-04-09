"""将「微型断路器」缩写统一为 MCB；确保「五孔插座」基础名存在（与 item-encoding-rules / 新模板一致）。"""


def execute():
	import frappe

	if frappe.db.exists("Item Base Name", "微型断路器"):
		frappe.db.set_value(
			"Item Base Name",
			"微型断路器",
			{"abbreviation": "MCB"},
			update_modified=True,
		)

	if not frappe.db.exists("Item Base Name", "五孔插座"):
		doc = frappe.get_doc(
			{
				"doctype": "Item Base Name",
				"base_name": "五孔插座",
				"abbreviation": "WKS",
				"description": "墙面五孔/错位五孔插座（非 DIN 导轨式）",
			}
		)
		if frappe.db.exists("Item Base Name", "电气件"):
			doc.parent_item_base_name = "电气件"
		doc.insert()

	frappe.db.commit()

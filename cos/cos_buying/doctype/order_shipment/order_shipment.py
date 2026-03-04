# Copyright (c) 2026, COS and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class OrderShipment(Document):
	"""订单运单：独立单据，多对一关联采购订单，避免与 ERPNext 内置 Shipment 冲突"""

	pass

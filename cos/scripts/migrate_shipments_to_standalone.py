# Copyright (c) 2026, COS and contributors
"""
将 Purchase Order Shipment 子表数据迁移到独立 Order Shipment 单据。
执行: bench --site <site> execute cos.scripts.migrate_shipments_to_standalone.migrate
"""
import frappe


def migrate():
	"""从 tabPurchase Order Shipment 迁移到 tabOrder Shipment"""
	if not frappe.db.table_exists("Purchase Order Shipment"):
		print("表 Purchase Order Shipment 不存在，跳过迁移")
		return
	if not frappe.db.table_exists("Order Shipment"):
		print("表 Order Shipment 不存在，请先执行 bench migrate")
		return
	rows = frappe.db.sql(
		"""
		SELECT parent, idx, courier_code, courier_name, tracking_no, phone,
		       status, last_track_time, track_detail, name
		FROM `tabPurchase Order Shipment`
		ORDER BY parent, idx
		""",
		as_dict=1,
	)
	created = 0
	for r in rows:
		if frappe.db.exists("Order Shipment", {"purchase_order": r.parent, "tracking_no": r.tracking_no}):
			continue
		doc = frappe.new_doc("Order Shipment")
		doc.purchase_order = r.parent
		doc.courier_code = r.courier_code
		doc.courier_name = r.courier_name
		doc.tracking_no = r.tracking_no
		doc.phone = r.phone
		doc.status = r.status
		doc.last_track_time = r.last_track_time
		doc.track_detail = r.track_detail
		doc.insert(ignore_permissions=True)
		created += 1
		print(f"  创建 Order Shipment: {doc.name} (PO: {r.parent})")
	print(f"迁移完成，共创建 {created} 条 Order Shipment")

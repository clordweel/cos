# Copyright (c) 2026, COS and contributors
"""
将旧 Shipment / Purchase Shipment 迁移到 Order Shipment。
若曾使用过 COS 的 Shipment 或 Purchase Shipment 单据，执行此脚本保留数据。
执行: bench --site <site> execute cos.scripts.migrate_shipment_to_order_shipment.migrate
"""
import frappe


def migrate():
	"""从 tabShipment 或 tabPurchase Shipment 迁移到 tabOrder Shipment"""
	created = 0
	for src_dt in ["Shipment", "Purchase Shipment"]:
		if not frappe.db.table_exists(src_dt):
			continue
		if not frappe.db.table_exists("Order Shipment"):
			print("表 Order Shipment 不存在，请先执行 bench migrate")
			return
		tab_name = "tab" + src_dt  # tabShipment 或 tabPurchase Shipment
		rows = frappe.db.sql(
			f"""
			SELECT name, purchase_order, company, courier_code, courier_name, tracking_no,
			       contact, phone, remarks, status, last_track_time, track_detail
			FROM `{tab_name}`
			WHERE purchase_order IS NOT NULL
			ORDER BY creation
			""",
			as_dict=1,
		)
		for r in rows:
			if frappe.db.exists("Order Shipment", {"purchase_order": r.purchase_order, "tracking_no": r.tracking_no}):
				continue
			doc = frappe.new_doc("Order Shipment")
			doc.purchase_order = r.purchase_order
			doc.company = r.company
			doc.courier_code = r.courier_code
			doc.courier_name = r.courier_name
			doc.tracking_no = r.tracking_no
			doc.contact = r.contact
			doc.phone = r.phone
			doc.remarks = r.remarks
			doc.status = r.status
			doc.last_track_time = r.last_track_time
			doc.track_detail = r.track_detail
			doc.insert(ignore_permissions=True)
			created += 1
			print(f"  迁移 Order Shipment: {doc.name} (原 {src_dt}: {r.name})")
	print(f"迁移完成，共创建 {created} 条 Order Shipment")

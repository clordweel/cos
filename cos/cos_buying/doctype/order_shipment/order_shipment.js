// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Order Shipment", {
	refresh: function (frm) {
		if (frm.doc.purchase_order) {
			frm.add_custom_button(__("查看采购订单"), function () {
				frappe.set_route("Form", "Purchase Order", frm.doc.purchase_order);
			});
		}
		// 若有轨迹缓存但无 HTML，从服务端刷新
		if (frm.doc.track_detail && !frm.doc.track_detail_html && !frm.doc.__islocal) {
			try {
				const detail = JSON.parse(frm.doc.track_detail);
				if (Array.isArray(detail) && detail.length) {
					const html = detail
						.map(
							(d) =>
								`<div class="track-item"><span class="text-muted">${d.time || d.ftime || ""}</span> ${d.context || ""}</div>`
						)
						.join("");
					frm.set_df_property("track_detail_html", "options", `<div class="track-detail">${html}</div>`);
				}
			} catch (e) {}
		}
	},
	purchase_order: function (frm) {
		if (frm.doc.purchase_order && !frm.doc.company) {
			frappe.db.get_value("Purchase Order", frm.doc.purchase_order, "company", (r) => {
				if (r && r.company) frm.set_value("company", r.company);
			});
		}
	},
	contact: function (frm) {
		if (frm.doc.contact && !frm.doc.phone) {
			frappe.db.get_value("Contact", frm.doc.contact, ["mobile_no", "phone"], (r) => {
				if (r && (r.mobile_no || r.phone)) {
					frm.set_value("phone", r.mobile_no || r.phone);
				}
			});
		}
	},
	query_btn: function (frm) {
		if (!frm.doc.courier_code || !frm.doc.tracking_no) {
			frappe.msgprint(__("请先填写快递公司代码和运单号"));
			return;
		}
		const code = (frm.doc.courier_code || "").split(" - ")[0].toLowerCase();
		if ((code === "shunfeng" || code === "sf") && !frm.doc.phone) {
			frappe.msgprint(__("顺丰快递需填写收/寄件人电话"));
			return;
		}
		frappe.call({
			method: "cos.cos_buying.express_tracking.refresh_order_shipment",
			args: { shipment: frm.doc.name },
			freeze: true,
			callback: function (r) {
				if (r.exc) return;
				if (r.message) {
					frm.set_value("status", r.message.status);
					frm.set_value("last_track_time", r.message.last_track_time);
					if (r.message.detail && r.message.detail.length) {
						frm.set_value("track_detail", JSON.stringify(r.message.detail));
					}
					if (r.message.track_detail_html) {
						frm.set_df_property("track_detail_html", "options", r.message.track_detail_html);
					}
					frm.refresh_fields();
				}
				if (r.message && r.message.detail && r.message.detail.length) {
					const msg = r.message.detail
						.map((d) => (d.context || "") + " " + (d.time || ""))
						.join("\n");
					frappe.msgprint({ title: __("物流轨迹"), message: msg });
				}
			},
		});
	},
});

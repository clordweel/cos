// Copyright (c) 2026, COS and contributors
// For license information, please see license.txt

function receipt_image_url(value) {
	if (!value) return "";
	if (value.startsWith("http://") || value.startsWith("https://")) return value;
	const path = value.startsWith("/") ? value : "/" + value;
	return window.location.origin + path;
}

function apply_receipt_preview_to_row(grid_row) {
	if (grid_row.grid.df.fieldname !== "receipt_images" || !grid_row.doc) return;
	const col = grid_row.columns_list && grid_row.columns_list.find((c) => c.df && c.df.fieldname === "receipt_image");
	if (!col || !col.static_area) return;
	const file_url = grid_row.doc.receipt_image;
	col.static_area.find(".receipt-preview-img").remove();
	if (file_url) {
		const src = receipt_image_url(file_url);
		const $img = $("<img />")
			.attr("src", src)
			.addClass("receipt-preview-img")
			.css({
				width: "40px",
				height: "40px",
				"object-fit": "cover",
				"border-radius": "4px",
				"margin-right": "6px",
				"vertical-align": "middle",
			})
			.on("error", function () {
				$(this).hide();
			});
		col.static_area.css("display", "flex").css("align-items", "center").prepend($img);
	}
}

frappe.ui.form.on("Order Shipment", {
	refresh: function (frm) {
		if (frm.doc.purchase_order) {
			frm.add_custom_button(__("查看采购订单"), function () {
				frappe.set_route("Form", "Purchase Order", frm.doc.purchase_order);
			});
		}
		// 签收凭证表格行渲染时，在「签收凭证」列显示缩略图预览
		const $wrapper = $(frm.wrapper);
		$wrapper.off("grid-row-render.receipt_preview").on("grid-row-render.receipt_preview", function (evt, grid_row) {
			apply_receipt_preview_to_row(grid_row);
		});
		const grid = frm.fields_dict.receipt_images && frm.fields_dict.receipt_images.grid;
		if (grid) {
			$(grid.wrapper).off("change.receipt_preview").on("change.receipt_preview", function () {
				setTimeout(function () {
					(grid.grid_rows || []).forEach(function (row) {
						apply_receipt_preview_to_row(row);
					});
				}, 150);
			});
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
		if (!frm.doc.logistics || !frm.doc.tracking_no) {
			frappe.msgprint(__("请先填写物流公司和运单号"));
			return;
		}
		if ((frm.doc.logistics === "shunfeng" || frm.doc.logistics === "sf") && !frm.doc.phone) {
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
					frm.refresh_fields();
				}
				if (r.message && r.message.detail && r.message.detail.length) {
					const esc = (s) =>
						(String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"));
					const html = r.message.detail
						.map(
							(d, i) => {
								const isLast = i === r.message.detail.length - 1;
								const border = isLast ? "" : "border-bottom: 1px solid var(--border-color);";
								return `<div class="track-popup-item" style="padding: 8px 0; ${border}"><span class="text-muted" style="font-size: 12px;">${esc(d.time || d.ftime)}</span><div style="margin-top: 4px;">${esc(d.context)}</div></div>`;
							}
						)
						.join("");
					const d = new frappe.ui.Dialog({
						title: __("物流轨迹"),
						size: "large",
						fields: [
							{
								fieldtype: "HTML",
								fieldname: "track_content",
								options: `<div style="max-height: 400px; overflow-y: auto; min-width: 400px; padding: 8px 0;">${html}</div>`,
							},
						],
					});
					d.show();
				}
			},
		});
	},
});

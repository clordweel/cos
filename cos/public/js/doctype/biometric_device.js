// Copyright (c) 2026, bit and contributors
// 考勤机：从设备读取用户列表、签到缓存等

function escape_html(s) {
	if (s === null || s === undefined) {
		return "";
	}
	return String(s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;");
}

function show_table_dialog(title, columns, rows) {
	const thead = `<tr>${columns.map((c) => `<th>${escape_html(c.label)}</th>`).join("")}</tr>`;
	const tbody = rows
		.map((row) => {
			const tds = columns.map((c) => `<td>${escape_html(row[c.field] ?? "")}</td>`).join("");
			return `<tr>${tds}</tr>`;
		})
		.join("");
	const html = `
<div style="max-height:420px;overflow:auto;font-size:12px;">
<table class="table table-bordered table-condensed" style="margin-bottom:0;">
<thead>${thead}</thead>
<tbody>${tbody}</tbody>
</table>
</div>
<p class="text-muted" style="margin-top:8px;">${__("共 {0} 条", [String(rows.length)])}</p>`;
	const d = new frappe.ui.Dialog({
		title: title,
		size: "large",
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
	});
	d.fields_dict.body.$wrapper.html(html);
	d.show();
}

frappe.ui.form.on("Biometric Device", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("连通探测"), () => {
			frappe.call({
				method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_probe",
				args: { device_name: frm.doc.name },
				freeze: true,
				freeze_message: __("正在连接设备…"),
				callback(r) {
					if (!r.message) {
						return;
					}
					const m = r.message;
					frappe.msgprint({
						title: __("探测结果"),
						message: __("用户数: {0}<br>缓存签到条数: {1}", [
							String(m.user_count ?? ""),
							String(m.attendance_count ?? ""),
						]),
						indicator: "green",
					});
				},
			});
		});

		frm.add_custom_button(__("读取用户列表"), () => {
			frappe.call({
				method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_fetch_users",
				args: { device_name: frm.doc.name },
				freeze: true,
				freeze_message: __("正在读取设备用户…"),
				callback(r) {
					const rows = r.message || [];
					if (!rows.length) {
						frappe.show_alert({ message: __("无用户数据"), indicator: "orange" });
						return;
					}
					show_table_dialog(
						__("设备用户"),
						[
							{ field: "uid", label: "UID" },
							{ field: "user_id", label: __("用户编号") },
							{ field: "name", label: __("姓名") },
							{ field: "privilege", label: __("权限") },
							{ field: "card", label: __("卡号") },
							{ field: "group_id", label: __("分组") },
						],
						rows,
					);
				},
			});
		});

		frm.add_custom_button(__("读取签到数据"), () => {
			const d = new frappe.ui.Dialog({
				title: __("读取签到缓存"),
				fields: [
					{
						fieldtype: "Int",
						fieldname: "min_year",
						label: __("最小年份过滤"),
						default: 2010,
						description: __("仅「仅有效记录」时生效"),
					},
					{
						fieldtype: "Int",
						fieldname: "limit",
						label: __("最多条数"),
						default: 200,
						description: __("最大 2000"),
					},
					{
						fieldtype: "Check",
						fieldname: "only_valid",
						label: __("仅有效记录"),
						default: 1,
						description: __("关闭则包含占位/异常时间等原始缓存"),
					},
				],
				primary_action_label: __("读取"),
				primary_action(values) {
					d.hide();
					frappe.call({
						method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_fetch_attendance",
						args: {
							device_name: frm.doc.name,
							min_year: values.min_year || 2010,
							limit: values.limit || 200,
							only_valid: values.only_valid ? 1 : 0,
						},
						freeze: true,
						freeze_message: __("正在读取签到…"),
						callback(r) {
							const rows = r.message || [];
							if (!rows.length) {
								frappe.show_alert({ message: __("无签到数据"), indicator: "orange" });
								return;
							}
							show_table_dialog(
								__("签到缓存"),
								[
									{ field: "user_id", label: __("用户编号") },
									{ field: "uid", label: "UID" },
									{ field: "timestamp", label: __("时间") },
									{ field: "status", label: __("状态") },
									{ field: "punch", label: __("打卡") },
								],
								rows,
							);
						},
					});
				},
			});
			d.show();
		});

		frm.add_custom_button(
			__("推送到 HRMS"),
			() => {
				frappe.confirm(__("将把设备缓存中有效签到写入 Employee Checkin，是否继续？"), () => {
					frappe.call({
						method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_push_attendance_to_hrms",
						args: { device_name: frm.doc.name },
						freeze: true,
						freeze_message: __("正在推送…"),
						callback(r) {
							const m = r.message || {};
							frappe.msgprint({
								title: __("推送结果"),
								message: m.summary || JSON.stringify(m),
								indicator: m.failed ? "orange" : "green",
							});
						},
					});
				});
			},
			__("同步"),
		);

		frm.add_custom_button(
			__("重启设备"),
			() => {
				frappe.confirm(__("将向设备发送重启指令，是否继续？"), () => {
					frappe.call({
						method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_device_restart",
						args: { device_name: frm.doc.name },
						freeze: true,
						callback() {
							frappe.show_alert({ message: __("已发送"), indicator: "green" });
						},
					});
				});
			},
			__("设备电源"),
		);

		frm.add_custom_button(
			__("关机"),
			() => {
				frappe.confirm(__("将向设备发送关机指令，是否继续？"), () => {
					frappe.call({
						method: "cos.cos_biometric.doctype.biometric_device.biometric_device.biometric_device_poweroff",
						args: { device_name: frm.doc.name },
						freeze: true,
						callback() {
							frappe.show_alert({ message: __("已发送"), indicator: "green" });
						},
					});
				});
			},
			__("设备电源"),
		);
	},
});

// Copyright (c) 2026, bit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Logto User Settings", {
	user: function(frm) {
		if (frm.doc.user) {
			// 获取 User 文档，查询其 social_logins 子表
			frappe.db.get_doc("User", frm.doc.user).then((user_doc) => {
				// 在 social_logins 子表中查找 provider 为 COS 的记录
				const cos_login = user_doc.social_logins?.find(
					login => login.provider && login.provider.toLowerCase().includes("cos")
				);
				
				if (cos_login && cos_login.userid) {
					// 提取该记录的 userid 字段，填充到表单的 user_id 字段
					frm.set_value("user_id", cos_login.userid);
				} else {
					// 如果没有找到记录，清空 user_id 字段
					frm.set_value("user_id", "");
					frappe.show_alert({
						message: __("该用户没有关联的 COS 社交登录记录"),
						indicator: 'orange'
					});
				}
			}).catch((error) => {
					frappe.show_alert({
						message: __("查询用户信息失败：{0}", [error.message || error]),
						indicator: 'red'
					});
					frm.set_value("user_id", "");
				});
		} else {
			// 如果清空了用户选择，则同时清空 user_id 字段
			frm.set_value("user_id", "");
		}
	},

	update_password: function(frm) {
		if (!frm.doc.user || !frm.doc.password) {
			frappe.msgprint(__("请确保已选择用户并输入了新密码"));
			return;
		}

		frappe.confirm(__("确定要更新用户 {0} 的密码吗？", [frm.doc.user]), () => {
			frm.call({
				doc: frm.doc,
				method: "update_logto_user_password",
				freeze: true,
				callback: function(r) {
					if (!r.exc && r.message && r.message.status === "success") {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						});
						// 清空密码字段并刷新
						frm.set_value("password", "");
						frm.refresh_field("password");
					}
				}
			});
		});
	}
});

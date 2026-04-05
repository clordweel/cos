// 侧栏底部用户区：官方 v16 模板为直达「用户」表单的链接，无下拉。
// 此处为头像区域补充「我的设置 / 注销」，与顶部应用菜单能力对齐。
// 仅初始化一次，避免重复 create_menu 叠加 document 监听。

frappe.provide("cos.desk_sidebar_user_menu");

cos.desk_sidebar_user_menu.setup = function () {
	const $btn = $(".sidebar-user-button");
	if (!$btn.length || $btn.data("cos-user-menu")) {
		return;
	}
	$btn.removeAttr("onclick");
	$btn.data("cos-user-menu", 1);
	frappe.ui.create_menu({
		parent: $btn,
		menu_items: [
			{
				label: __("My Settings"),
				icon: "user",
				action: "frappe.ui.toolbar.route_to_user()",
			},
			{
				label: __("Logout"),
				icon: "logout",
				action: "frappe.app.logout()",
			},
		],
	});
};

$(document).on("app_ready", function () {
	setTimeout(function () {
		cos.desk_sidebar_user_menu.setup();
	}, 0);
});

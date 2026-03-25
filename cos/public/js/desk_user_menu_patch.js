// 修复 Desk 侧栏中 #toolbar-user 下拉无菜单项：
// Frappe v16 中 make_nav_bar()（触发 toolbar_setup）早于 make_sidebar()，若用户下拉壳在侧栏模板内，
// 则不会在 toolbar_setup 阶段被填充，导致 dropdown-menu 为空。此处用 boot 中的 navbar_settings 补渲染。

frappe.provide("cos.desk_user_menu");

cos.desk_user_menu.populate_if_empty = function () {
	const $menu = $("#toolbar-user");
	if (!$menu.length || $menu.children().length) {
		return;
	}
	const settings = frappe.boot && frappe.boot.navbar_settings;
	const items = settings && settings.settings_dropdown;

	if (items && items.length) {
		items.forEach(function (item) {
			if (item.hidden) {
				return;
			}
			if (item.route) {
				$("<a>", { class: "dropdown-item", href: item.route, text: __(item.item_label) }).appendTo(
					$menu
				);
			} else if (item.action) {
				$("<a>", { class: "dropdown-item", href: "#", text: __(item.item_label) })
					.attr("onclick", "return " + item.action)
					.appendTo($menu);
			} else {
				$("<div>", { class: "dropdown-divider" }).appendTo($menu);
			}
		});
		return;
	}

	// Navbar 未配置 settings_dropdown 时的最小可用菜单
	$("<a>", { class: "dropdown-item", href: "#", text: __("My Settings") })
		.on("click", function (e) {
			e.preventDefault();
			frappe.ui.toolbar.route_to_user();
		})
		.appendTo($menu);

	if (frappe.boot.session_defaults && frappe.boot.session_defaults.length) {
		$("<a>", { class: "dropdown-item", href: "#", text: __("Session Defaults") })
			.on("click", function (e) {
				e.preventDefault();
				frappe.ui.toolbar.setup_session_defaults();
			})
			.appendTo($menu);
	}

	$("<a>", { class: "dropdown-item", href: "#", text: __("Reload") })
		.on("click", function (e) {
			e.preventDefault();
			frappe.ui.toolbar.clear_cache();
		})
		.appendTo($menu);

	$("<a>", { class: "dropdown-item", href: "#", text: __("Logout") })
		.on("click", function (e) {
			e.preventDefault();
			frappe.app.logout();
		})
		.appendTo($menu);
};

$(document).on("app_ready", function () {
	// 侧栏 DOM 在 app_ready 时已挂载；短延迟兜底异步路由/侧栏刷新
	setTimeout(function () {
		cos.desk_user_menu.populate_if_empty();
	}, 0);
	setTimeout(function () {
		cos.desk_user_menu.populate_if_empty();
	}, 150);
});

$(document).on("sidebar_setup", function () {
	setTimeout(function () {
		cos.desk_user_menu.populate_if_empty();
	}, 0);
});

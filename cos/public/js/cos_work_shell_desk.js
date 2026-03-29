// Cos Work App WebView 打开 Desk：按当前 path 拉取 nav_bar_inset_mode，与 Website Worker Portal 同源逻辑。
(function () {
	if (!/\bCosWorkApp\b/i.test(navigator.userAgent || "")) {
		return;
	}

	function applyInsetMode(mode) {
		document.documentElement.setAttribute("data-cos-work-app-shell", "1");
		document.documentElement.setAttribute(
			"data-cos-shell-inset-mode",
			mode || "safe_area"
		);
	}

	// 与 `get_nav_bar_inset_for_path` / COS Work Mini Program.launch_path 对齐的保守首帧猜测，
	// 避免 frappe.ready 前整页按 safe_area 排版；API 返回后仍会覆盖。
	function defaultInsetModeForPathname() {
		var p = window.location.pathname || "";
		if (/stock-reconciliation/i.test(p)) {
			return "app_bar";
		}
		var trimmed = p.replace(/\/+$/, "") || "/";
		if (trimmed === "/app" || trimmed === "/desk" || /^\/desk\//.test(p)) {
			return "app_bar";
		}
		return "safe_area";
	}

	applyInsetMode(defaultInsetModeForPathname());

	function callApi() {
		if (typeof frappe === "undefined" || !frappe.call) {
			applyInsetMode(defaultInsetModeForPathname());
			return;
		}
		frappe.call({
			method: "cos.worker_portal_shell_context.get_nav_bar_inset_for_path",
			args: { path: window.location.pathname || "" },
			callback: function (r) {
				var m =
					r.message && r.message.nav_bar_inset_mode
						? r.message.nav_bar_inset_mode
						: "safe_area";
				applyInsetMode(m);
			},
			error: function () {
				applyInsetMode(defaultInsetModeForPathname());
			},
		});
	}

	if (typeof frappe !== "undefined" && frappe.ready) {
		frappe.ready(callApi);
	} else {
		window.addEventListener("load", function () {
			if (typeof frappe !== "undefined" && frappe.ready) {
				frappe.ready(callApi);
			} else {
				applyInsetMode(defaultInsetModeForPathname());
			}
		});
	}
})();

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

	function callApi() {
		if (typeof frappe === "undefined" || !frappe.call) {
			applyInsetMode("safe_area");
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
				applyInsetMode("safe_area");
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
				applyInsetMode("safe_area");
			}
		});
	}
})();

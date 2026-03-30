// Cos Work App WebView 打开 Desk：按当前 path 拉取 nav_bar_inset_mode，与 Website Worker Portal 同源逻辑。
(function () {
	if (!/\bCosWorkApp\b/i.test(navigator.userAgent || "")) {
		return;
	}

	/** 与 Frappe `theme_switcher.js`：`data-theme-mode` + `frappe.ui.set_theme()`；无 frappe 时回退 `html.dark`。 */
	function applyCosShellThemeFromQuery() {
		try {
			var params = new URLSearchParams(window.location.search || "");
			var t = (params.get("__cos_theme") || "").trim().toLowerCase();
			if (t !== "light" && t !== "dark" && t !== "system") {
				return;
			}
			var r = document.documentElement;
			var deskMode = t === "system" ? "automatic" : t;
			r.setAttribute("data-cos-theme", t);
			if (window.__cosShellThemeListener) {
				try {
					window
						.matchMedia("(prefers-color-scheme: dark)")
						.removeEventListener("change", window.__cosShellThemeListener);
				} catch (e) {}
				window.__cosShellThemeListener = null;
			}
			function applyTailwindFallback() {
				var d =
					t === "dark" ||
					(t === "system" &&
						window.matchMedia("(prefers-color-scheme: dark)").matches);
				r.classList.toggle("dark", d);
				try {
					if (document.body) document.body.classList.toggle("dark", d);
				} catch (e) {}
			}
			function applyFrappeDeskTheme() {
				if (
					typeof frappe === "undefined" ||
					!frappe.ui ||
					typeof frappe.ui.set_theme !== "function"
				) {
					return false;
				}
				r.setAttribute("data-theme-mode", deskMode);
				frappe.ui.set_theme();
				return true;
			}
			function setupSystemListener() {
				if (t !== "system") return;
				var listener = function () {
					if (
						typeof frappe !== "undefined" &&
						frappe.ui &&
						typeof frappe.ui.set_theme === "function"
					) {
						frappe.ui.set_theme();
					} else {
						applyTailwindFallback();
					}
				};
				window.__cosShellThemeListener = listener;
				window
					.matchMedia("(prefers-color-scheme: dark)")
					.addEventListener("change", listener);
			}
			function run() {
				if (applyFrappeDeskTheme()) {
					setupSystemListener();
					return;
				}
				applyTailwindFallback();
				setupSystemListener();
			}
			if (typeof frappe !== "undefined" && frappe.ready) {
				frappe.ready(run);
			} else {
				run();
			}
		} catch (e) {}
	}

	applyCosShellThemeFromQuery();

	function applyCosShellCompanyFromQuery() {
		try {
			var params = new URLSearchParams(window.location.search || "");
			var c = (params.get("__cos_company") || "").trim();
			if (!c) return;
			document.documentElement.setAttribute("data-cos-company", c);
			window.__COS_WORK_APP_COMPANY__ = c;
		} catch (e) {}
	}

	applyCosShellCompanyFromQuery();

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

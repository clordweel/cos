app_name = "cos"
app_title = "COS"
app_publisher = "bit"
app_description = "Collaborative Operating System"
app_email = "dev@bit.js.cn"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "cos",
        "logo": "/assets/cos/images/cos_logo_light_t.svg",
        "title": "COS",
        "route": "/app/cos",
        "has_permission": "cos.cos.check_app_permission",
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/cos/css/cos_custom.css",
    "/assets/cos/css/cos_work_shell_inset.css",
]
app_include_js = [
    "/assets/cos/js/cos_work_shell_desk.js",
    "/assets/cos/js/cos_custom.js",
    "/assets/cos/js/desk_user_menu_patch.js",
    "/assets/cos/js/update_items_float_patch.js",
    "/assets/cos/js/sub_form_json_tools.js",
    "/assets/cos/js/text_editor_source_toggle.js",
    "/assets/cos/js/doctype/purchase_tax_update.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/cos/css/cos.css"
# web_include_js = "/assets/cos/js/cos.js"

# Worker Portal SPA 路由（已批待 JE 已简化移除，应付转员工请在 Desk PI 上操作）
website_route_rules = [
	{"from_route": "/worker-portal/pi-reimbursement-pending/<path:id>", "to_route": "worker-portal/pi-reimbursement-pending"},
	{"from_route": "/worker-portal/pi-reimbursement-pending", "to_route": "worker-portal/pi-reimbursement-pending"},
	{"from_route": "/worker-portal/pi-reimbursement-approval", "to_route": "worker-portal/pi-reimbursement-approval"},
]


def extend_website_context_for_worker_portal(context):
	"""Worker Portal 资源版本号 + Cos Work App 壳顶栏占位（路径匹配 COS Work Mini Program）。"""
	import os

	import frappe

	from cos.worker_portal_shell_context import (
		is_cos_work_app_shell_query,
		is_cos_work_app_shell_user_agent,
		nav_bar_inset_mode_or_default,
		resolve_nav_bar_inset_mode_for_path,
	)

	try:
		path = frappe.get_app_path("cos", "public", "worker_portal", "worker-portal.js")
		if os.path.isfile(path):
			context["cos_wp_asset_ver"] = str(int(os.path.getmtime(path)))
		else:
			context["cos_wp_asset_ver"] = "0"
	except Exception:
		context["cos_wp_asset_ver"] = "0"

	try:
		css_path = frappe.get_app_path("cos", "public", "css", "cos_work_shell_inset.css")
		if os.path.isfile(css_path):
			context["cos_shell_inset_css_ver"] = str(int(os.path.getmtime(css_path)))
		else:
			context["cos_shell_inset_css_ver"] = "0"
	except Exception:
		context["cos_shell_inset_css_ver"] = "0"

	req = getattr(frappe.local, "request", None)
	req_path = ""
	ua = ""
	req_args = None
	if req is not None:
		req_path = getattr(req, "path", "") or ""
		try:
			ua = frappe.request.headers.get("User-Agent", "") or ""
		except Exception:
			ua = ""
		try:
			req_args = getattr(req, "args", None)
		except Exception:
			req_args = None
	context["cos_is_work_app_shell"] = is_cos_work_app_shell_user_agent(
		ua
	) or is_cos_work_app_shell_query(req_args)
	resolved = resolve_nav_bar_inset_mode_for_path(req_path)
	context["cos_nav_bar_inset_mode"] = nav_bar_inset_mode_or_default(resolved)


update_website_context = [
	"cos.hooks.extend_website_context_for_worker_portal",
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "cos/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Item Group": "public/js/doctype/item_group.js",
    "Item": "public/js/doctype/item.js",
    "Company": "public/js/doctype/company.js",
    # 发票：创建税务登记入口
    "Sales Invoice": "public/js/doctype/invoice_tax_registry.js",
    "Purchase Invoice": "public/js/doctype/invoice_tax_registry.js",
    # 采购运单：物流查询
    "Purchase Order": "public/js/doctype/purchase_order.js",
    # 物料需求单：提交后 Update Items 变更明细
    "Material Request": "public/js/doctype/material_request.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "cos/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "cos.utils.jinja_methods",
# 	"filters": "cos.utils.jinja_filters"
# }

# Installation
# ------------

before_install = ["cos.setup.coa_setup.copy_custom_charts"]
after_install = ["cos.setup.uom_setup.setup_uom_data"]

# Uninstallation
# ------------

before_uninstall = ["cos.setup.coa_setup.remove_custom_charts"]
# after_uninstall = "cos.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "cos.utils.before_app_install"
# after_app_install = "cos.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "cos.utils.before_app_uninstall"
# after_app_uninstall = "cos.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cos.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Company": {
        "validate": "cos.cos_accounts.utils.company_tax_validation.validate_company_tax_accounts",
    },
    "New Item Request": {
        "before_save": "cos.cos_stock.utils.new_item_request.calculate_parameters_hash",
    },
    # Item 物料：恢复 ERPNext 默认编码逻辑，不再由 COS 在 before_insert 中改写 item_code / naming_series
    # 如需自定义编码，请通过单独脚本或 Agent 规范，而不是全局 Hook。
    "Project": {
        "before_insert": "cos.cos_stock.utils.project.auto_set_project_code",
    },
    "Address": {
        "before_save": "cos.cos_share.utils.address.update_address_display",
        "validate": "cos.cos_share.utils.address.update_address_display",
    },
    # 当发票被税务登记引用时，取消/删除需联动处理（避免链接校验拦截）
    # 员工垫付：提交后手动创建 JE 应付转员工，取消时自动取消已关联 JE
    "Purchase Invoice": {
        "validate": [
            "cos.cos_accounts.utils.purchase_invoice_general_tax.on_purchase_invoice_validate_general_tax",
            "cos.cos_accounts.utils.employee_advance_payable_transfer.on_purchase_invoice_validate",
        ],
        "before_cancel": "cos.cos_accounts.utils.employee_advance_payable_transfer.purchase_invoice_before_cancel",
        "on_trash": "cos.cos_accounts.utils.tax_registry_reference.invoice_on_trash",
    },
    # 付给员工 PE 提交/取消时，更新 PI 的 custom_employee_reimbursed
    "Payment Entry": {
        "on_submit": "cos.cos_accounts.utils.employee_advance_payable_transfer.payment_entry_on_submit",
        "on_cancel": "cos.cos_accounts.utils.employee_advance_payable_transfer.payment_entry_on_cancel",
    },
    "Delivery Note": {
        "on_submit": "cos.cos_accounts.utils.delivery_note_auto_invoice.on_delivery_note_submit",
    },
    "Purchase Order": {
        "before_save": "cos.cos_buying.purchase_order_ecommerce.on_purchase_order_before_save",
        "validate": "cos.cos_accounts.utils.employee_advance_payable_transfer.validate_purchase_order_advance_employee",
    },
    # 虚拟占位物料（custom_is_virtual_item）仅允许草稿，提交前必须转换为真实物料
    # 提交后变更明细时校验 qty >= ordered_qty，变更完成后更新 indented_qty
    "Material Request": {
        "before_submit": "cos.cos_stock.utils.material_request.validate_no_virtual_items_in_material_request",
        "before_update_after_submit": "cos.cos_stock.material_request_order_change.validate_mr_item_qty_on_update",
        "on_update_after_submit": "cos.cos_stock.material_request_order_change.on_mr_update_after_submit",
    },
    "Sales Invoice": {
        "before_cancel": "cos.cos_accounts.utils.tax_registry_reference.invoice_before_cancel",
        "on_trash": "cos.cos_accounts.utils.tax_registry_reference.invoice_on_trash",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"cos.tasks.all"
# 	],
# 	"daily": [
# 		"cos.tasks.daily"
# 	],
# 	"hourly": [
# 		"cos.tasks.hourly"
# 	],
# 	"weekly": [
# 		"cos.tasks.weekly"
# 	],
# 	"monthly": [
# 		"cos.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "cos.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
#     # "Purchase Order": "cos.cos_accounts.overrides.currency_ext.RMBMixin",
# }

# override_doctype_class = {}

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.desk.search.search_link": "cos.cos_share.controllers.search.custom_search_link",
    "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice": "cos.cos_accounts.overrides.purchase_invoice_from_po.make_purchase_invoice",
    "erpnext.stock.doctype.material_request.material_request.make_purchase_order": "cos.cos_buying.purchase_order_ecommerce.make_purchase_order",
    "erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier": "cos.cos_buying.purchase_order_ecommerce.make_purchase_order_based_on_supplier",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "cos.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["cos.utils.before_request"]
# after_request = ["cos.utils.after_request"]

# Job Events
# ----------
# before_job = ["cos.utils.before_job"]
# after_job = ["cos.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

on_login = ["cos.cos_logto.controllers.oauth2_handler.on_login"]
on_session_creation = ["cos.cos_logto.controllers.oauth2_handler.on_login"]

# Worker Portal: Bearer token 鉴权（替代 cookies，解决 iOS WebView 问题）
# normalize_session_user_none_to_guest 必须排在 validate 之后，避免 wpt 无效时会话仍为 None
auth_hooks = [
	"cos.worker_portal_api.validate_worker_portal_token",
	"cos.worker_portal_api.normalize_session_user_none_to_guest",
]

# auth_hooks = [
# 	"cos.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
    {
        "dt": "Report",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts", "COS Buying"]]],
    },
    {
        "dt": "Client Script",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {
        "dt": "Server Script",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {"dt": "Source Type", "filters": [["module", "in", ["COS Share", "COS Buying"]]]},
    {"dt": "Logistics Company", "filters": [["module", "=", "COS Buying"]]},
    {"dt": "Item Parameter Template", "filters": [["module", "=", "COS Stock"]]},
    {"dt": "Item Base Name", "filters": [["name", "in", ["虚拟", "切削液"]]]},
    {"dt": "External Link", "filters": [["module", "=", "COS Share"]]},
    {"dt": "Currency", "filters": [["name", "in", ["CNY"]]]},
    {
        "dt": "Financial Report Template",
        "filters": [["module", "in", ["COS Accounts"]]],
    },
    {
        "dt": "Print Format",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts", "COS Buying"]]],
    },
    {"dt": "Print Style", "filters": [["name", "in", ["COS 通用打印样式"]]]},
    {
        "dt": "Letter Head",
        "filters": [["name", "in", ["COS 通用打印页头"]]],
    },
    {"dt": "Address Template", "filters": [["name", "in", ["China"]]]},
    {
        "dt": "Terms and Conditions",
        "filters": [
            [
                "name",
                "in",
                [
                    "采购合同条款 - POT/2026-10",
                    "销售合同条款 - SOT/2026-10",
                    "工业品采销合同补充条款",
                ],
            ]
        ],
    },
    {
        "dt": "Property Setter",
        "filters": [
            [
                "doc_type",
                "in",
                [
                    "New Item Request",
                    "Item Parameter Template",
                    "Item Group",
                    "Item",
                    "UOM",
                    "Material Request Item",
                    "Purchase Order Item",
                    "Purchase Receipt Item",
                    "Purchase Invoice Item",
                    "Supplier Quotation Item",
                    "Quotation Item",
                    "Sales Order Item",
                    "Delivery Note",
                    "Delivery Note Item",
                    "Sales Invoice",
                    "Sales Invoice Item",
                    "Purchase Receipt",
                    "Stock Entry Detail",
                    "BOM Item",
                    "BOM Explosion Item",
                    "Project",
                ],
            ],
        ],
    },
    {
        "dt": "Custom Field",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Buying", "COS Accounts"]]],
    },
    {
        "dt": "Role",
        "filters": [["name", "in", ["Logto User"]]],
    },
    {
        "dt": "Custom DocPerm",
        "filters": [["role", "in", ["Logto User"]]],
    },
    {
        "dt": "UOM",
        "filters": [
            [
                "name",
                "in",
                [
                    "件",
                    "张",
                    "台",
                    "根",
                    "卷",
                    "箱",
                    "盒",
                    "支",
                    "片",
                    "组",
                    "桶",
                    "袋",
                    "包",
                    "块",
                    "只",
                    "次",
                    "条",
                    "排",
                    "百/件",
                    "千/件",
                ],
            ]
        ],
    },
    {
        "dt": "COS Work Mini Program",
        "filters": [
            [
                "program_id",
                "in",
                [
                    "pi_reimbursement_pending",
                    "pi_reimbursement_approval",
                    "stock_reconciliation",
                    "desk_home",
                ],
            ]
        ],
    },
    {
        "dt": "COS Work Mini Program Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "CWMPR-ALL-PI-PENDING",
                    "CWMPR-ALL-PI-APPR",
                    "CWMPR-ALL-STOCK",
                    "CWMPR-ALL-DESK",
                ],
            ]
        ],
    },
]

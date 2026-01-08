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
]
app_include_js = [
    # "/assets/cos/js/v16_link_hotfix.js",
    "/assets/cos/js/cos_custom.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/cos/css/cos.css"
# web_include_js = "/assets/cos/js/cos.js"

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
    "New Item Request": {
        "before_save": "cos.cos_stock.utils.new_item_request.calculate_parameters_hash",
    },
    "Item": {
        "before_insert": "cos.cos_stock.utils.item.auto_set_item_code",
        # "validate": "cos.cos_accounts.utils.tax_logic.update_item_tax_data",
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

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.desk.search.search_link": "cos.cos_share.controllers.search.custom_search_link",
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
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {
        "dt": "Client Script",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {
        "dt": "Server Script",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {"dt": "Source Type", "filters": [["module", "=", "COS Share"]]},
    {"dt": "Item Parameter Template", "filters": [["module", "=", "COS Stock"]]},
    {"dt": "External Link", "filters": [["module", "=", "COS Share"]]},
    {"dt": "Currency", "filters": [["name", "in", ["CNY"]]]},
    {
        "dt": "Financial Report Template",
        "filters": [["module", "in", ["COS Accounts"]]],
    },
    {
        "dt": "Letter Head",
        "filters": [["name", "in", ["COS Standard"]]],
    },
    {
        "dt": "Print Format",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
    },
    {"dt": "Print Style", "filters": [["name", "in", ["COS Standard"]]]},
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
                    "Delivery Note Item",
                    "Sales Invoice Item",
                    "Stock Entry Detail",
                    "BOM Item",
                    "BOM Explosion Item",
                ],
            ],
        ],
    },
    {
        "dt": "Custom Field",
        "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]],
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
                    "块",
                    "只",
                    "次",
                    "百/件",
                    "千/件",
                ],
            ]
        ],
    },
]

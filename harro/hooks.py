app_name = "harro"
app_title = "Harro"
app_publisher = "Fosserp"
app_description = "Custom App"
app_email = "viral@fosserp.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "harro",
# 		"logo": "/assets/harro/logo.png",
# 		"title": "Harro",
# 		"route": "/harro",
# 		"has_permission": "harro.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/harro/css/harro.css"
app_include_js = [
    "/assets/harro/js/frappe/views/gantt/gantt_view.js",
    "/assets/harro/js/harro_hierarchy_chart.bundle.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/harro/css/harro.css"
# web_include_js = "/assets/harro/js/harro.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "harro/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
        "BOM Creator" : "public/js/bom_creator.js",
        "Project" : "public/js/project.js",
        "Activity Type" : "public/js/activity_type.js",
        "Job Card" : "public/js/job_card.js",
        "Stock Entry" : "public/js/stock_entry.js",
        "Purchase Receipt" : "public/js/purchase_receipt.js",
        "Sales Invoice" : "public/js/sales_invoice.js",
        "Delivery Note" : "public/js/delivery_note.js",
        "Purchase Invoice" : "public/js/purchase_invoice.js",
        "Sales Order" : "public/js/sales_order.js",
        "Purchase Order" : "public/js/purchase_order.js",
        "Expense Claim" : "public/js/expense_claim.js",
        "Task" : "public/js/task.js",
        "Production Plan" : "public/js/production_plan.js",
        "Material Request" : "public/js/material_requiest.js",
        "Request for Quotation" : "public/js/request_for_quotation.js"
    }

doctype_list_js = {"Task" : "public/js/task_list.js"}
doctype_calendar_js = {"Task" : "public/js/task_calender.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "harro/public/icons.svg"

# Home Pages
# ----------
after_migrate = "harro.harro.custom_field.create_custom_fields_on_migrate"
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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "harro.utils.jinja_methods",
# 	"filters": "harro.utils.jinja_filters"
# }
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["module" , "=" , "Harro"]
        ]
    }
]
# Installation
# ------------

# before_install = "harro.install.before_install"
# after_install = "harro.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "harro.uninstall.before_uninstall"
# after_uninstall = "harro.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "harro.utils.before_app_install"
# after_app_install = "harro.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "harro.utils.before_app_uninstall"
# after_app_uninstall = "harro.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "harro.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"BOM Creator": "harro.harro.override.bom_creator.CustomBOMCreator",
    "Production Plan" : "harro.harro.docevents.production_plan.CustomProductionPlan"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
    "Work Order": {
        "after_insert": "harro.harro.docevents.work_order.enqueue_fetch_row_material"
    },
    "Purchase Order" : {
        "validate" : "harro.harro.docevents.purchase_order.validate"
    },
    "Job Card" : {
        "on_submit" : "harro.harro.docevents.job_card.on_submit",
        "on_cancel" : "harro.harro.docevents.job_card.on_cancel",
        "validate" : "harro.harro.docevents.job_card.validate",
    },
    "Timesheet" : {
        "on_submit" : "harro.harro.docevents.timesheet.on_submit",
        "on_cancel" : "harro.harro.docevents.timesheet.on_cancel",
        "validate" : "harro.harro.docevents.timesheet.validate",
    },
    "Project" : {
        "validate" : "harro.harro.docevents.project.validate"
    },
    "Task" : {
        "validate" : "harro.harro.docevents.task.validate",
        "on_update" : "harro.harro.docevents.task.update_parent_task_dependency_status"
    },
    "Material Request": {
        "on_update": "harro.harro.docevents.material_request.on_update",
        "validate" : "harro.harro.docevents.material_request.validate",
    },
    "Employee Checkin" : {
        "after_insert" : "harro.harro.docevents.employee_checkin.after_insert"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"harro.tasks.all"
# 	],
# 	"daily": [
# 		"harro.tasks.daily"
# 	],
# 	"hourly": [
# 		"harro.tasks.hourly"
# 	],
# 	"weekly": [
# 		"harro.tasks.weekly"
# 	],
# 	"monthly": [
# 		"harro.tasks.monthly"
# 	],
# }

scheduler_events = {
	"cron" : {
        "*/15 * * * *" : [
            "harro.harro.api.update_the_task_timer_based_on_shift_end",
            "harro.harro.api.update_the_job_card_timer_based_on_shift_end",
        ],
        "*/5 * * * *" : [
            "harro.harro.docevents.task.update_task_timer",
            "harro.harro.api.stop_timer_for_jobcard_every_two_hours"
        ],
    }
}

# Testing
# -------

# before_tests = "harro.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.buying.doctype.purchase_order.purchase_order.make_subcontracting_order": "harro.harro.docevents.purchase_order.make_subcontracting_order",
    "erpnext.subcontracting.doctype.subcontracting_order.subcontracting_order.make_subcontracting_receipt" : "harro.harro.docevents.subcontracting_order.make_subcontracting_receipt",
    "erpnext.manufacturing.doctype.production_plan.production_plan.get_items_for_material_requests" : "harro.harro.docevents.production_plan.get_items_for_material_requests",
    "erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry": "harro.harro.override.work_order.make_stock_entry",
    "erpnext.controllers.subcontracting_controller.make_rm_stock_entry" : "harro.harro.override.subcontracting_order.make_rm_stock_entry",
    "erpnext.stock.doctype.material_request.material_request.make_purchase_order": "harro.harro.override.material_request.make_purchase_order"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "harro.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["harro.utils.before_request"]
# after_request = ["harro.utils.after_request"]

# Job Events
# ----------
# before_job = ["harro.utils.before_job"]
# after_job = ["harro.utils.after_job"]

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

# auth_hooks = [
# 	"harro.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


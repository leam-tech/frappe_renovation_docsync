# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "frappe_renovation_docsync"
app_title = "Frappe Renovation Docsync"
app_publisher = "Leam Technology Systems"
app_description = "Extensions for Frappe Event Streams"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@leam.ae"
app_license = "MIT"

fixtures = [
  {
    "dt": "Custom Field",
    "filters": [
      ["app_name", "=", "frappe_renovation_docsync"]
    ]
  }
]

override_whitelisted_methods = {
  'frappe.event_streaming.doctype.event_consumer.event_consumer.register_consumer': 'frappe_renovation_docsync.utils.event_consumer.register_consumer'
}

has_permission = {
  "Event Update Log": "frappe_renovation_docsync.utils.update_log.consumer_perm_check"
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frappe_renovation_docsync/css/frappe_renovation_docsync.css"
# app_include_js = "/assets/frappe_renovation_docsync/js/frappe_renovation_docsync.js"

# include js, css files in header of web template
# web_include_css = "/assets/frappe_renovation_docsync/css/frappe_renovation_docsync.css"
# web_include_js = "/assets/frappe_renovation_docsync/js/frappe_renovation_docsync.js"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "frappe_renovation_docsync.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "frappe_renovation_docsync.install.before_install"
# after_install = "frappe_renovation_docsync.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappe_renovation_docsync.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappe_renovation_docsync.tasks.all"
# 	],
# 	"daily": [
# 		"frappe_renovation_docsync.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappe_renovation_docsync.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappe_renovation_docsync.tasks.weekly"
# 	]
# 	"monthly": [
# 		"frappe_renovation_docsync.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "frappe_renovation_docsync.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappe_renovation_docsync.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "frappe_renovation_docsync.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


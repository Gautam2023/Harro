# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions


def execute(filters=None):
	if not filters:
		filters = {}
	elif filters.get("from_date") or filters.get("to_date"):
		filters["from_time"] = "00:00:00"
		filters["to_time"] = "24:00:00"

	columns = get_column()
	conditions = get_conditions(filters)

	data = get_data(conditions, filters)

	return columns, data


def get_column():
	return [
		_("Timesheet") + ":Link/Timesheet:120",
		_("Employee") + "::150",
		_("Employee Name") + "::150",
		_("From Datetime") + "::140",
		_("To Datetime") + "::140",
		_("Hours") + "::70",
		_("Activity Type") + "::120",
		_("Task") + ":Link/Task:150",
		_("Project") + ":Link/Project:120",
		_("Status") + "::70",
	]


def get_data(conditions, filters):
    time_sheet = frappe.db.sql(
        """
        SELECT 
            ts.name,
            ts.employee,
            ts.employee_name,
            tsd.from_time,
            tsd.to_time,
            tsd.hours,
            tsd.activity_type,
            tsd.task,
            tsd.project,
            ts.status
        FROM `tabTimesheet Detail` tsd
        INNER JOIN `tabTimesheet` ts ON tsd.parent = ts.name
        LEFT JOIN `tabActivity Type` at ON at.name = tsd.activity_type
        WHERE {conditions}
        ORDER BY ts.name
        """.format(conditions=conditions),
        filters,
        as_list=1,
    )

    return time_sheet


def get_conditions(filters):
	conditions = "ts.docstatus = 1"
	if filters.get("from_date"):
		conditions += " and tsd.from_time >= timestamp(%(from_date)s, %(from_time)s)"
	if filters.get("to_date"):
		conditions += " and tsd.to_time <= timestamp(%(to_date)s, %(to_time)s)"
	if filters.get("unproductiove_hours"):
		conditions += " and at.custom_unproductive_work = %(unproductiove_hours)s"
	if filters.get("activity_type"):
		conditions += " and tsd.activity_type = %(activity_type)s"
	if filters.get("project"):
		conditions += " and tsd.project = %(project)s"
	if filters.get("employee"):
		conditions += " and ts.employee = %(employee)s"
	match_conditions = build_match_conditions("Timesheet")
	if match_conditions:
		conditions += " and %s" % match_conditions

	return conditions

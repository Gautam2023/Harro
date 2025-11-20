// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.query_reports["Hoefliger Timesheet Summery"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "activity_type",
			label: __("Activity Type"),
			fieldtype: "Link",
			options: "Activity Type",
		},
		{
			fieldname: "unproductiove_hours",
			label: __("Unproductiove Hours"),
			fieldtype: "Check"
		},

	],
};
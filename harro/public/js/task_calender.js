// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.views.calendar["Task"] = {
	field_map: {
		start: "exp_start_date",
		end: "exp_end_date",
		id: "name",
		title: "subject",
		allDay: "allDay",
		progress: "progress",
		actual_start : "act_start_date",
		actual_end : "act_end_date"
 	},
	gantt: true,
	filters: [
		{
			fieldtype: "Link",
			fieldname: "project",
			options: "Project",
			label: __("Project"),
		},
	],
	get_events_method: "frappe.desk.calendar.get_events",
};

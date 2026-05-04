// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.query_reports["Travel MIS Report"] = {
	filters: [
        {
            fieldname: "ba_number",
            label: "BA Number",
            fieldtype: "Link",
            options: "Project"
        },
        {
            fieldname: "travel_request",
            label: "Travel Request",
            fieldtype: "Link",
            options: "Travel Request"
        },
        {
            fieldname: "travel_plan",
            label: "Travel Plan",
            fieldtype: "Link",
            options: "Travel Planning"
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date"
        },
        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "travel_type",
            label: "Travel Type",
            fieldtype: "Select",
            options: ["","Domestic","International"]
        }
    ]
};

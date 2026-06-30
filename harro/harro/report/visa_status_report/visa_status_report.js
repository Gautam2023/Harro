// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.query_reports["Visa Status Report"] = {
	"filters": [
		{"label": "Country", "fieldname": "country", "fieldtype": "Link", "options": "Country"},
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee"}
	]
};


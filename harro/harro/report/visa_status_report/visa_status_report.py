# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	# columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns() -> list[dict]:
	return [
		{"label": "Country", "fieldname": "country", "fieldtype": "Link", "options": "Country", "width": 120},
		{"label": "Employee Name", "fieldname": "employee_name" ,"fieldtype": "Data", "width": 200},
		# {"label": "Employee Id", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee"},
		{"label": "Valid From", "fieldname": "valid_from", "fieldtype": "Date", "width": 120},
		{"label": "Valid To", "fieldname": "valid_to", "fieldtype": "Date", "width": 120},
		{"label": "Entry Type", "fieldname": "entry_type", "fieldtype": "Data"}
	]


def get_data(filters=None) -> list[dict]:
	conditions = []
	values = {}
	if filters:
		if filters.get("country"):
			conditions.append("evd.visa_country = %(country)s")
			values["country"] = filters["country"]
		
		if filters.get("employee"):
			conditions.append("emp.name = %(employee)s")
			values["employee"] = filters["employee"]

	where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	return frappe.db.sql(f"""
		SELECT
			emp.employee_name,
			emp.name as employee_id,
			evd.visa_country as country,
			evd.from as valid_from,
			evd.to as valid_to,
			evd.entry as entry_type
		FROM
			`tabEmployee` emp
		JOIN
			`tabEmployee Visa Details` evd ON emp.name = evd.parent
		{where_clause}
	""", values=values, as_dict=True)


	

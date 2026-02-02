# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Travel Plan ID", "fieldname": "name", "fieldtype": "Link", "options": "Travel Planning", "width": 140},
        {"label": "Travel Request ID", "fieldname": "travel_request", "fieldtype": "Link", "options": "Travel Request", "width": 180},
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Data", "width": 160},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},

        {"label": "Is Claimable", "fieldname": "is_claimable", "fieldtype": "Check", "width": 100},
        {"label": "Not Claimable", "fieldname": "not_claimable", "fieldtype": "Check", "width": 120},

        {"label": "Onward Travel Date", "fieldname": "onward_date", "fieldtype": "Date"},
        {"label": "Return Travel Date", "fieldname": "return_date", "fieldtype": "Date"},

        {"label": "Onward Flight Cost", "fieldname": "onward_flight_cost", "fieldtype": "Currency"},
        {"label": "Return Flight Cost", "fieldname": "return_flight_cost", "fieldtype": "Currency"},
        {"label": "Seat Charges", "fieldname": "seat_charges", "fieldtype": "Currency"},
        {"label": "Hotel Cost", "fieldname": "hotel_cost", "fieldtype": "Currency"},
        {"label": "Taxi Cost", "fieldname": "taxi_cost", "fieldtype": "Currency"},

        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency"},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency"},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency"},

        {"label": "Claimable Amount", "fieldname": "claimable_amount", "fieldtype": "Currency"},
        {"label": "Non Claimable Amount", "fieldname": "unclaimed_amount", "fieldtype": "Currency"}
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters and filters.get('ba_number'):
        conditions.append("tp.ba_number = %(ba_number)s")
        values["ba_number"] = filters["ba_number"]
        
    if filters and filters.get('travel_request'):
        conditions.append("tped.travel_request = %(travel_request)s")
        values["travel_request"] = filters["travel_request"]
        
    if filters and filters.get('travel_plan'):
        conditions.append("tp.name = %(travel_plan)s")
        values["travel_plan"] = filters["travel_plan"]
        
    if filter and filters.get('from_date'):
        conditions.append("tped.custom_onward_travel_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
        
    if filter and filters.get('to_date'):
        conditions.append("tped.custom_return_travel_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]
        
        
    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = "WHERE " + condition_str

    data = frappe.db.sql(f"""
		SELECT
			tp.name,
			tped.travel_request,
			tped.employee_hh_id AS employee,
			tped.employee_name,
			tped.custom_is_claimable AS is_claimable,
			tped.custom_not_claimable AS not_claimable,
            tped.custom_onward_travel_date as onward_date,
            tped.custom_return_travel_date as return_date,
			tped.custom_onward_flight_cost AS onward_flight_cost,
			tped.custom_return_flight_cost AS return_flight_cost,
			tped.custom_seat_charges AS seat_charges,
			tped.hotel_coast,
			tped.taxi_coast,
            ed.total_amount,
			ed.paid_amount,
            ed.outstanding_amount,
            ed.claimed_amount,
            ed.unclaimed_amount
		FROM `tabTravel Planning` tp
		LEFT JOIN `tabTravel Planning Employee Details` tped ON tp.name = tped.parent
        LEFT JOIN `tabExpense Details` ed ON ed.parent = tp.name
		{condition_str}
	""", values, as_dict=True)

    return data



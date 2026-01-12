# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_link_to_form


@frappe.whitelist()
def create_travel_plan(names):
	travel_request = eval(names)
	travel_planing_list = []
	travel_planing = frappe.new_doc("Travel Planning")

	for row in travel_request:
		tr_doc = frappe.get_doc("Travel Request", row)
		if tr_doc.docstatus < 1:
			frappe.throw("Travel Request should be submitted.<br><ul><li>{0}</li></ul>".format(get_link_to_form('Travel Request', row)))
		if len(tr_doc.itinerary):
			for tr in tr_doc.itinerary:
				travel_planing.append("travel_itinerary", {
					"travel_request" : tr_doc.name,
					"employee_hh_id" : tr_doc.employee,
					"employee_name" : tr_doc.employee_name,
					"travel_from" : tr.travel_from,
					"travel_to" : tr.travel_to,
					"mode_of_travel" : tr.mode_of_travel,
					"extra_baggage" : tr.custom_extra_baggage
				})
		else:
			travel_planing.append("travel_itinerary", {
				"travel_request" : tr_doc.name,
				"employee_hh_id" : tr_doc.employee,
				"employee_name" : tr_doc.employee_name,
			})
		
		if employee := frappe.db.exists("Employee", {"user_id" : frappe.session.user}):
			travel_planing.travel_requestor = employee

		travel_planing.travel_type = tr_doc.travel_type
		travel_planing.purpose_of_travel = tr_doc.purpose_of_travel

	if travel_request:
		travel_planing.ba_number = tr_doc.custom_ba_number
	
	travel_planing.insert()

	travel_planing_list.append(travel_planing.name)

	message = """ <p>Travel Planning is Created.</p> """
	message += "<ul>"
	for tp in travel_planing_list:
		message += f"<li>{get_link_to_form('Travel Planning', tp)}</li>"
	message += "</ul>"
	frappe.msgprint(message)
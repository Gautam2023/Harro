# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_link_to_form


@frappe.whitelist()
def create_travel_plan(names):
	travel_request = eval(names)
	skipped = []
	to_create = []

	for req in travel_request:
		plan = frappe.db.get_value(
			"Travel Planning Employee Details",
			{"travel_request": req},
			"parent"
		)
		if plan:
			skipped.append((req, plan))
		else:
			to_create.append(req)

	if not to_create:
		msg = "<p>Travel Planning already exists for selected requests:</p><ul>"
		for req, plan in skipped:
			msg += f"<li>{get_link_to_form('Travel Request', req)} → {get_link_to_form('Travel Planning', plan)}</li>"
		msg += "</ul>"
		frappe.throw(msg)

	travel_plan = frappe.new_doc("Travel Planning")
	for req in to_create:
		tr_doc = frappe.get_doc("Travel Request", req)
		# if tr_doc.docstatus < 1:
		# 	frappe.throw(
		# 		"Travel Request should be submitted.<br><ul><li>{0}</li></ul>".format(
		# 			get_link_to_form('Travel Request', req)
		# 		)
		# 	)
		if tr_doc.docstatus == 0:
			tr_doc.workflow_state = "Trip Planned"
			tr_doc.save(ignore_permissions=True)

		if len(tr_doc.itinerary):
			for tr in tr_doc.itinerary:
				travel_plan.append("travel_itinerary", {
					"travel_request" : tr_doc.name,
					"employee_hh_id" : tr_doc.employee,
					"employee_name" : tr_doc.employee_name,
					"travel_from" : tr.travel_from,
					"travel_to" : tr.travel_to,
					"mode_of_travel" : tr.mode_of_travel,
					"extra_baggage" : tr.custom_extra_baggage,
					"check_in_date" : tr.check_in_date,
					"check_out_date" : tr.check_out_date,
					"room_night" : tr.room_night,
					"lodging_required" : tr.lodging_required,
					"preferred_area_for_lodging" : tr.preferred_area_for_lodging,
					"travel_request_itinerary": tr.name,
					"custom_onward_travel_date": tr.custom_onward_travel_date,
					"custom_return_travel_date": tr.custom_return_travel_date,
					"custom_taxi_required": tr.custom_taxi_required
				})
		else:
			travel_plan.append("travel_itinerary", {
				"travel_request" : tr_doc.name,
				"employee_hh_id" : tr_doc.employee,
				"employee_name" : tr_doc.employee_name,
			})
	
	if employee := frappe.db.exists("Employee", {"user_id" : frappe.session.user}):
			travel_plan.travel_requestor = employee

	travel_plan.travel_type = tr_doc.travel_type
	travel_plan.purpose_of_travel = tr_doc.purpose_of_travel

	if travel_request:
		travel_plan.ba_number = tr_doc.custom_ba_number

	if to_create:
		travel_plan.ba_number = tr_doc.custom_ba_number

	travel_plan.insert()

	msg = "<p>Travel Planning Created:</p>"
	msg += f"<ul><li>{get_link_to_form('Travel Planning', travel_plan.name)}</li></ul>"

	if skipped:
		msg += "<p><b>Information:</b> A Travel Plan already exists for the following Travel Requests : </p><ul>"
		for req, plan in skipped:
			msg += f"<li>{get_link_to_form('Travel Request', req)} → {get_link_to_form('Travel Planning', plan)}</li>"
		msg += "</ul>"

	frappe.msgprint(msg)



@frappe.whitelist()
def get_flight_purchase_invoice_defaults(employee_row, travel_doc):
    import json

    if isinstance(employee_row, str):
        employee_row = json.loads(employee_row)

    row = frappe._dict(employee_row)

    ba_number = frappe.get_value("Travel Planning", travel_doc, "ba_number")

    mandatory_fields = {
        "Vendor Name": row.get("custom_flight_booking_vendor"),
        "Bill No": row.get("custom_flight_invoice_id"),
        "BA Number": ba_number,
        "Service Type": row.get("custom_service_type"),
        "Total Amount": row.get("custom_total_flight_cost_as_per_invoice")
    }

    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    if missing_fields:
        frappe.throw(f"Mandatory field(s) missing: {', '.join(missing_fields)}")

    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": row.custom_flight_booking_vendor,
        "travel_planning": travel_doc,
        "bill_no": row.custom_flight_invoice_id,
        "project": ba_number
    })

    doc.append("items", {
        "item_code": row.custom_service_type,
        "qty": 1,
        "rate": row.custom_total_flight_cost_as_per_invoice
    })

    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True

    doc.insert()

    attachments = [
        row.get("custom_onward_flight_invoice_attachment"),
        row.get("custom_return_flight_invoice_attachment")
    ]

    for file_url in attachments:
        if file_url:
            frappe.get_doc({
                "doctype": "File",
                "file_url": file_url,
                "attached_to_doctype": "Purchase Invoice",
                "attached_to_name": doc.name
            }).insert(ignore_permissions=True)

    return doc.name


@frappe.whitelist()
def get_hotel_purchase_invoice_defaults(employee_row, travel_doc):
    import json

    if isinstance(employee_row, str):
        employee_row = json.loads(employee_row)

    row = frappe._dict(employee_row)

    ba_number = frappe.get_value("Travel Planning", travel_doc, "ba_number")

    mandatory_fields = {
        "Vendor Name": row.get("custom_hotel_booking_vendor_name"),
        "Bill No": row.get("custom_hotel_invoice_id"),
        "BA Number": ba_number,
		"Service Type": row.get("custom_service_category"),
		"Total Amount": row.get("custom_total_hotel_charge")
    }

    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    if missing_fields:
        frappe.throw(f"Mandatory field(s) missing: {', '.join(missing_fields)}")

    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": row.custom_hotel_booking_vendor_name,
        "travel_planning": travel_doc,
        "bill_no": row.custom_hotel_invoice_id,
        "project": ba_number,
		"custom_supplier_invoice": row.custom_taxi_bill
    })

    doc.append(
        "items",
        {
            "item_code": row.custom_service_category,
            "qty": 1,
            "rate": row.custom_total_hotel_charge
        }
    )

    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True

    doc.save()

    return doc.name
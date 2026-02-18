# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class TravelInsuranceApplicationDetails(Document):
	pass


def add_item(source, target, source_parent):
	if source.service_item:
		target.append("items", {
			"item_code": source.service_item,
			"rate": source.cost
		})


@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Travel Insurance Application Details",
		source_name,
		{
			"Travel Insurance Application Details": {
				"doctype": "Purchase Invoice", 
				"field_map" : {
					"name" : "travel_insurance_application_details",
					"vendor_name": "supplier"
				},
				"postprocess": add_item
			},
		},
		target_doc,
	)

	return doclist
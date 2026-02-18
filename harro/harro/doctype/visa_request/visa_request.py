# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class VisaRequest(Document):
	pass


@frappe.whitelist()
def get_visa_check_list_details(chekck_list):
	return frappe.get_doc("Country Wise visa Document Checklist", chekck_list)




def add_item(source, target, source_parent):
	if source.custom_service_type:
		target.append("items", {
			"item_code": source.custom_service_type,
			"rate": source.custom_cost
		})


@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Visa Request",
		source_name,
		{
			"Visa Request": {
				"doctype": "Purchase Invoice", 
				"field_map" : {
					"name" : "visa_request",
					"custom_vendor_name": "supplier"
				},
				"postprocess": add_item
			},
		},
		target_doc,
	)

	return doclist
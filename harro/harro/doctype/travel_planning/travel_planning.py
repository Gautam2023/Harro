# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class TravelPlanning(Document):
    pass




@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Travel Planning",
		source_name,
		{
			"Travel Planning": {
				"doctype": "Purchase Invoice", 
				"field_map" : {
					"name" : "travel_planning"
				}
			},
		},
		target_doc,
	)

	return doclist
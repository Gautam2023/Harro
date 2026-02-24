# Copyright (c) 2025, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class Taxi(Document):
	pass

@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Taxi",
		source_name,
		{
			"Taxi": {
				"doctype": "Purchase Invoice",
				"field_map": {
					"name": "taxi",
					"custom_supplier": "supplier"
				}
			},
		},
		target_doc
	)
	return doclist
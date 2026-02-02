# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VisaRequest(Document):
	pass


@frappe.whitelist()
def get_visa_check_list_details(chekck_list):
	return frappe.get_doc("Country Wise visa Document Checklist", chekck_list)
# Copyright (c) 2026, Fosserp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RMBatchdetails(Document):
	def validate(self):
		self.invoice_no = frappe.db.get_value("Batch", self.batch_no, "invoice_no")
		self.bill_of_entry = frappe.db.get_value("Batch", self.batch_no, "bill_of_entry")

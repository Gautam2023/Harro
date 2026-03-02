import frappe
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest

class CustomPaymentRequest(PaymentRequest):

    def create_payment_entry(self, submit=True):

        # Always get UNSAVED document
        payment_entry = super().create_payment_entry(submit=False)

        payment_entry.custom_company_contact = self.custom_company_contact

        return payment_entry
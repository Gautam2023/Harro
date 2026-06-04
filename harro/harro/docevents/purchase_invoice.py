import frappe
from frappe.utils import getdate
from erpnext.controllers.accounts_controller import get_payment_terms


def fix_due_date_based_on_posting_date(doc, method=None):
    use_posting_date = frappe.db.get_single_value(
        "Accounts Settings",
        "due_date_calculation_not_based_on_supplier_invoice_no"
    )

    if not use_posting_date:
        return

    # Set bill_date = posting_date so validate_due_date uses posting_date as base
    doc.bill_date = getdate(doc.posting_date)

    # Force clear payment_schedule so set_payment_schedule() recalculates it
    # from bill_date (now = posting_date) instead of keeping frontend values
    doc.payment_schedule = []
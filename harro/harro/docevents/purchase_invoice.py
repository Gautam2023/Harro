import frappe
from frappe.utils import getdate


def fix_due_date_based_on_posting_date(doc, method=None):
    use_posting_date = frappe.db.get_single_value(
        "Accounts Settings",
        "due_date_calculation_not_based_on_supplier_invoice_no"
    )

    # checkbox = 0 → do nothing, ERPNext works normally
    if not use_posting_date:
        return

    # checkbox = 1 → set bill_date = posting_date
    # ERPNext will then naturally calculate due_date from posting_date
    # using the payment term's credit_days
    doc.bill_date = getdate(doc.posting_date)
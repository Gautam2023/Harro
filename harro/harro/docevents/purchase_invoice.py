import frappe

from erpnext.accounts.party import get_due_date

def fix_due_date_based_on_posting_date(doc, method=None):
    use_posting_date = frappe.db.get_single_value(
        "Accounts Settings",
        "due_date_calculation_not_based_on_supplier_invoice_no"
    )

    if not use_posting_date:
        return
    
    doc.due_date = get_due_date(
        doc.posting_date,
        "Supplier",
        doc.supplier,
        doc.company,
        None,
        template_name = doc.payment_terms_template,
    )

    doc.ignore_default_payment_terms_template = 1

    for schedule in doc.payment_schedule:
        schedule.due_date = doc.due_date

# def set_due_date(doc, method=None):
#     for item in doc.items:
#         if not item.purchase_receipt:
#             continue

#         pr_due_date = frappe.db.get_value(
#             "Purchase Receipt", 
#             item.purchase_receipt, 
#             "custom_due_date"
#         )

#         if pr_due_date:
#             doc.due_date = pr_due_date
#             break
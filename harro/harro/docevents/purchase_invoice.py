import frappe

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
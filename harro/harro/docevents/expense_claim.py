import frappe

def validate(doc, method):
    if doc.custom_expense_claim_type == "Forex Credit Card":
        for row in doc.expenses:
            if not row.custom_multi_currency or not row.custom_exchange_rate:
                frappe.throw("Please set Multi Currency & Exchange Rate")
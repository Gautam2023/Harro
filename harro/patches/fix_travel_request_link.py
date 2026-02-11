import frappe

def execute():
    frappe.db.set_value(
        "DocField",
        {
            "parent": "Visa Request",
            "fieldname": "travel_request"
        },
        "options",
        "Travel Request"
    )

    frappe.clear_cache(doctype="Visa Request")

# harro/harro/docevents/material_request.py
import frappe
from frappe.desk.form.assign_to import add as assign_to

def on_update(doc, method):
    """
    Auto-assign Material Request to the linked user in Item Group
    """
    if doc.item_group:
        item_group = frappe.get_doc("Item Group", doc.item_group)
        user = item_group.get("user")

        if user:
            assign_to({
                "doctype": "Material Request",
                "name": doc.name,
                "assign_to": [user],
                "description": "Auto-assigned based on Item Group"
            })

import frappe

def execute():
    frappe.get_doc({
        "is_system_generated": 1,
        "doctype_or_field": "DocField",
        "doc_type": "Task",
        "field_name": "status",
        "property": "options",
        "property_type": "Small Text",
        "value": "Open\nWorking\nPending Review\nOverdue\nTemplate\nCompleted\nCancelled\nWork In Progress\nOn Hold",
        "doctype": "Property Setter"
    }).insert()
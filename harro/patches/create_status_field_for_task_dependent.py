import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Task Depends On" : [
            {
                "fieldname" : "custom_status",
                "label" : "Status",
                "read_only" : 1,
                "fieldtype" : "Data",
                "insert_after" : "subject"
            }
        ]
    }
    create_custom_fields(fields)
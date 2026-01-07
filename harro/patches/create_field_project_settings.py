import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Projects Settings" : [
            {
                "fieldname" : "task_cut_of_time",
                "label" : "Task Cut of Time",
                "fieldtype" : "Float",
            },
            {
                "fieldname" : "job_card_cut_of_time",
                "label" : "Job Card Cut of Time",
                "fieldtype" : "Float",
            }
        ]
    }

    create_custom_fields(fields)

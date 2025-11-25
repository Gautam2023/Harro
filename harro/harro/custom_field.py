import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_custom_fields_on_migrate():
    fields = {
        "Timesheet Detail" : [
            {
                "insert_after" : "completed",
                "fieldname" : "employee",
                "label" : "Employee",
                "fieldtype" : "Link",
                "options" : "Employee",
            }
        ],
        "Timesheet" : [
            {
                "insert_after" : "parent_project",
                "fieldname" : "job_card",
                "label" : "Job Card",
                "fieldtype" : "Link",
                "options" : "Job Card",
                "read_only" :  1
            }
        ],
        "Task" : [
            {
                "insert_after" : "depends_on",
                "fieldname" : "unproductive_work_timelogs",
                "label" : "Time Log",
                "fieldtype" : "Table",
                "options" : "Timesheet Detail",
                "hidden" :  1
            },
            {
                "insert_after" : "status",
                "fieldname" : "working_status",
                "label" : "Working Status",
                "fieldtype" : "Select",
                "options" : "\nWork In Progress\nOn Hold",
                "hidden" :  1
            }
        ],
        "HR Settings" : [
            {
                "insert_after" : "retirement_age",
                "fieldname" : "task_permissable_limit",
                "label" : "Task Permissable Limit",
                "fieldtype" : "Float",
                "hidden" :  0
            }
        ],
        "Material Request" : [
            {
                "label": "structure_class_head",
                "fieldname": "custom_structure_class_head",
                "insert_after": "custom_ba_number",
                "fieldtype": "Link",
                "options": "Structure Class Head"
            }
        ]
    }

    create_custom_fields(fields)
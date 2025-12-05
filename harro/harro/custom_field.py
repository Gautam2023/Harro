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
        "Item Group" : [
            {
                "insert_after" : "is_group",
                "fieldname" : "user",
                "label" : "User",
                "fieldtype" : "Link",
                "options" : "User"
            }
        ],
        "Material Request" : [
            {
                "insert_after" : "custom_ba_number",
                "fieldname" : "item_group",
                "label" : "Item Group",
                "fieldtype" : "Link",
                "options" : "Item Group"
            }
        ],
        "Production Plan" : [
            {
                "insert_after" : "transfer_materials",
                "fieldname" : "remove_based_item_group",
                "label" : "Commodity Group",
                "fieldtype" : "Table MultiSelect",
                "options" : "Removed As Per Item Group",
                "description" : "Update the Commodity Group to remove items from below table"
            },
            {
                "label": "Delete Selected Commodity Group Items",
                "fieldname": "delete_selected_commodity_group_items",
                "insert_after": "remove_based_item_group",
                "fieldtype": "Button",
            }
        ],
        "Material Request Plan Item" : [
            {
                "label": "Commodity Group",
                "fieldname": "commodity_group",
                "insert_after": "item_code",
                "fieldtype": "Link",
                "options" : "Item Group",
                "read_only" : 1,
                "fetch_from" : "item_code.item_group"
            }
        ]
    }

    create_custom_fields(fields)
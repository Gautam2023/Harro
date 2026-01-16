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
            },
            {
                "label": "Actual Progress",
                "fieldname": "custom_actual_progress",
                "insert_after": "act_end_date",
                "fieldtype": "Color",
                "default" : "#FFC067"
            },
            {
                "label": "Extra Days of Effort",
                "fieldname": "extra_days",
                "insert_after": "expected_time",
                "fieldtype": "Data",
                "read_only" : 1,
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
            },
            {
                "insert_after" : "items",
                "fieldname" : "total_items",
                "label" : "Total Number of Items",
                "fieldtype" : "Data",
                "read_only" : 1
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
                "read_only" : 0,
                "fetch_from" : "item_code.item_group"
            }
        ],
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
        ],
        "Activity Type" : [
            {
                "fieldname" : "parent_activity_type",
                "label" : "Parent Activity",
                "fieldtype" : "Link",
                "options" : "Parent Activity",
                "insert_after" : "custom_unproductive_work"
            }
        ],
        "Travel Planning" : [
            {
                "fieldname" : "travel_requestor",
                "label" : "Travel Requestor",
                "fieldtype" : "Link",
                "options" : "Employee",
                "insert_after" : "travel_plan"
            }
        ],
        "Job Card Time Log" : [
            {
                "fieldname" : "activity_type",
                "label" : "Activity Type",
                "fieldtype" : "Link",
                "options" : "Activity Type",
                "insert_after" : "employee",
                "in_list_view" : 1
            }
        ],
        "Project" : [
            {
                "fieldname" : "custom_org_chart",
                "label" : "Org Chart",
                "fieldtype" : "Tab Break",
            },
            {
                "fieldname" : "custom_chart",
                "label" : "Chart",
                "fieldtype" : "HTML",
                "insert_after" : "custom_org_chart"
            }
        ]
        
    }

    create_custom_fields(fields)
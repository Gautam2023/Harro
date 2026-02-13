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
            },
            {
                "label": "Deleted Selected Commodity Group Items",
                "fieldname": "deleted_selected_commodity_group_items",
                "insert_after": "delete_selected_commodity_group_items",
                "fieldtype": "Check",
                "hidden" : 1
            },
            {
                "insert_after" : "ignore_existing_ordered_qty",
                "fieldname" : "items_to_reduce_qty",
                "label" : "Items To Reduce Quantity",
                "fieldtype" : "Table MultiSelect",
                "options" : "Item To Reduce Quantity",
                "description" : "Update the Sub Assembly Item to reduce item from below table"
            },
            {
                "label" : "Reduce Item From Raw Material",
                "fieldname" : "reduce_item_from_raw_material",
                "insert_after" : "items_to_reduce_qty",
                "fieldtype" : "Button"
            },
            {
                "label" : "Removed Reduce Item From Raw Material",
                "fieldname" : "removed_reduce_item_from_raw_material",
                "insert_after" : "reduce_item_from_raw_material",
                "fieldtype" : "Check",
                "hidden" : 1
            },
            {
                "insert_after" : "skip_available_sub_assembly_item",
                "fieldname" : "remove_from_sub_and_raw",
                "label" : "Remove From Sub Assembly and Raw Material",
                "fieldtype" : "Table MultiSelect",
                "options" : "Item To Reduce Quantity"
            },
            {
                "label" : "Remove Sub-Assembly and Raw Materials",
                "fieldname" : "reduce_items",
                "insert_after" : "remove_from_sub_and_raw",
                "fieldtype" : "Button"
            },

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
        "Purchase Invoice" : [
            {
                "fieldname" : "travel_planning",
                "label" : "Travel Planning",
                "fieldtype" : "Link",
                "options" : "Travel Planning",
                "insert_after" : "due_date"
            }
        ],
        "Purchase Receipt Item" : [
            {
                "fieldname" : "ordered_qty_",
                "label" : "Ordered Qty",
                "fieldtype" : "Float",
                "insert_after" : "received_qty"
            }
        ],
        "Travel Itinerary" : [
            {
                "fieldname" : "room_night",
                "label" : "Room Night",
                "fieldtype" : "Int",
                "insert_after" : "check_out_date",
                "depends_on" : "eval:doc.lodging_required == 1;"
            }
        ],
        "Operation" : [
            {
                "fieldname" : "department",
                "label" : "Department",
                "fieldtype" : "Link",
                "insert_after" : "is_corrective_operation",
                "options" : "Department",
            }
        ],
        "Production Plan Sub Assembly Item" : [
            {
                "fieldname" : "structure_class",
                "label" : "Structure Class Head",
                "fieldtype" : "Data",
                "insert_after" : "supplier",
                "read_only" : 1,
                "fetch_from" : "production_item.custom_structure_class_head"
            }
        ],
        "Item" : [
            {
                "fieldname" : "is_allowed_without_po",
                "label" : "Is Allowed Without PO",
                "fieldtype" : "Check",
                "insert_after" : "is_grouped_asset"
            }
        ],
        "Travel Planning Employee Details": [
            {
            "fieldname": "reference_section",
            "label": "Reference Section",
            "fieldtype": "Section Break",
            "insert_after": "custom_taxi_required"
            },
            {
            "fieldname": "travel_request_itinerary",
            "label": "Travel Request Itinerary",
            "fieldtype": "Data",
            "insert_after": "reference",
            "hidden" : 1
            }
        ],
        "Expense Details" : [
            {
                "fieldname": "create_purchase_invoice",
                "label": "Create Purchase Invoice",
                "fieldtype": "Button",
                "insert_after": "profit"
            }
        ],
        "Taxi" : [
            {
                "fieldname": "taxi_requestor",
                "label": "Taxi Requestor",
                "fieldtype": "Link",
                "options": "Employee",
                "insert_after": "is_paid"
            },
            {
                "fieldname": "taxi_requester_name",
                "label": "Taxi Requester Name",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "taxi_requestor",
                "fetch_from": "taxi_requestor.employee_name"
            },
            {
                "fieldname": "taxi_requester_email",
                "label": "Taxi Requestor Email",
                "fieldtype": "Data",
                "options": "Email",
                "read_only": 1,
                "insert_after": "taxi_requester_name",
                "fetch_from": "taxi_requestor.user_id"
            }
        ],
        "Stock Entry Detail" : [
            {
                "fieldname": "section_bil_invoice",
                "label": "",
                "fieldtype": "Section Break",
                "read_only": 0,
            },
            {
                "fieldname": "invoice_no",
                "label": "Invoice No",
                "fieldtype": "Data",
                "read_only": 0,
                "insert_after" : "section_bil_invoice"
            },
            {
                "fieldname": "column_bil_invoice",
                "label": "",
                "fieldtype": "Column Break",
                "insert_after" : "invoice_no"
            },
            {
                "fieldname": "bill_of_entry",
                "label": "Bill of Entry",
                "fieldtype": "Data",
                "read_only": 0,
                "insert_after" : "column_bil_invoice"
            },
            {
                "fieldname": "section_bil_invoice_closed",
                "label": "",
                "fieldtype": "Section Break",
                "read_only": 0,
                "insert_after" : "bill_of_entry"
            },
        ],
        "Expense Details" :[
            {
               "fieldname": "invoice_attachment",
               "label": "Invoice Attachment",
               "fieldtype": "Attach",
               "insert_after": "service_type" 
            }
        ]
        
    }

    create_custom_fields(fields)

    if frappe.get_meta("Project").has_field("custom_org_chart"):
        frappe.db.delete("Custom Field", "Project-custom_org_chart")

    if frappe.get_meta("Project").has_field("custom_chart"):
        frappe.db.delete("Custom Field", "Project-custom_chart")

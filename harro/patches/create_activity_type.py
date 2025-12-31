import frappe

def execute():
    activity_type = [
        "Reached Permissable Work Hours",
        "Check Out",
        "Shift End",
    ]

    for row in activity_type:
        if not frappe.db.exists("Activity Type", row):
            frappe.get_doc({
                "doctype" : "Activity Type",
                "activity_type" : row
            }).insert()
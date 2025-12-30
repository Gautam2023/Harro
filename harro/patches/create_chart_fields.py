from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields_on_migrate()
    
def create_custom_fields_on_migrate():
    fields = {
        "Project" : [
            {
                "insert_after" : "message",
                "fieldname" : "org_chart",
                "label" : "Org Chart",
                "fieldtype" : "Tab Break",
            },
            {
                "insert_after" : "org_chart",
                "fieldname" : "chart",
                "label" : "",
                "fieldtype" : "HTML",
            }
        ]
    }

    create_custom_fields(fields)
import frappe

def execute():
    task_list = frappe.db.get_list("ToDo", {
        "status" : "Open",
        "reference_type" : "Task",
    }, pluck="reference_name")

    for row in task_list:
        doc = frappe.get_doc("Task", row)
        frappe.share.add_docshare(
			doc.doctype, doc.name, doc.custom_assigned_to_responsible_user, write=1, share=0, flags={"ignore_share_permission": True}
		)


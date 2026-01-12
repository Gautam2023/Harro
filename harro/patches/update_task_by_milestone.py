import frappe

def execute():

    # Get all non-template tasks
    tasks = frappe.get_all(
        "Task",
        filters={
            "status": ["!=", "Template"]
        },
        fields=["name", "subject"]
    )

    for task in tasks:
        if not task.subject:
            continue

        # Check if a matching Template milestone task exists
        template_task_exists = frappe.db.exists(
            "Task",
            {
                "status": "Template",
                "is_milestone": 1,
                "subject": task.subject
            }
        )

        if template_task_exists:
            frappe.db.set_value(
                "Task",
                task.name,
                "is_milestone",
                1,
                update_modified=False
            )

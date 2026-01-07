import frappe

def execute():
    frappe.logger().info("Starting Task dependency status backfill")

    links = frappe.get_all(
        "Task Depends On",
        fields=["parent", "task"]
    )

    parents = {}

    # group by parent
    for link in links:
        parents.setdefault(link.parent, set()).add(link.task)

    for parent_name, task_names in parents.items():
        parent_task = frappe.get_doc("Task", parent_name)
        updated = False

        task_status_map = {
            t.name: t.status
            for t in frappe.get_all(
                "Task",
                filters={"name": ["in", list(task_names)]},
                fields=["name", "status"]
            )
        }

        for dep in parent_task.depends_on:
            status = task_status_map.get(dep.task)
            if status and dep.custom_status != status:
                dep.custom_status = status
                updated = True

        if updated:
            parent_task.flags.ignore_permissions = True
            parent_task.flags.ignore_validate = True
            parent_task.save()

    frappe.db.commit()
    frappe.logger().info("Task dependency status backfill completed")

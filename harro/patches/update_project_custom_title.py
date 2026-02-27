import frappe
def execute():
    projects = frappe.get_all(
        "Project",
        fields = ["name", "custom_ba_number", "project_name"]
    )

    for p in projects:
        custom_ba_number = p.custom_ba_number or ""
        project_name = p.project_name or ""

        if custom_ba_number and project_name:
            title = f"{custom_ba_number} - {project_name}"
        else:
            title = custom_ba_number or project_name or ""

        frappe.db.set_value("Project", p.name, "custom_title", title)

    frappe.db.commit()
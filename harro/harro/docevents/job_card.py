import frappe
import json
from harro.harro.docevents.project import calculate_project_working_hours


def validate(self, method):
    if self.project and not self.is_new():
        calculate_project_working_hours(self.project)

def on_submit(self, method):
    if self.project:
        calculate_project_working_hours(self.project)

def on_cancel(self, method):
    if self.project:
        calculate_project_working_hours(self.project)


@frappe.whitelist()
def update_unproductive_log(arg, job_card):
    args = json.loads(arg)
    doc = frappe.get_doc("Job Card", job_card)

    employees = doc.employee

    if employees:
        for emp in employees:
            doc.append("custom_unproductive_work_timelogs", {
                "activity_type": args.get("activity_type"),
                "from_time": args.get("from_time"),
                "project": args.get("project"),
                "task": args.get("task"),
                "employee": emp.employee  # update employee field in child table row
            })
    else:
        # No employees → add single entry
        doc.append("custom_unproductive_work_timelogs", {
            "activity_type": args.get("activity_type"),
            "from_time": args.get("from_time"),
            "project": args.get("project"),
            "task": args.get("task"),
        })

    doc.flags.ignore_permissions = True
    doc.save()

    return {"status": "success"}


@frappe.whitelist()
def resume_unproductive_log(to_time, job_card):
    doc = frappe.get_doc("Job Card", job_card)

    # Last log entry
    last_log = doc.custom_unproductive_work_timelogs[-1]
    last_log.to_time = to_time
    doc.flags.ignore_permissions = True

    employees = doc.get("employee") or []

    # If employees exist: create timesheet per employee
    if employees:
        for emp in employees:

            # Create Timesheet for each employee
            timesheet_doc = frappe.get_doc({
                "doctype": "Timesheet",
                "employee": emp,
                "parent_project": doc.project,
                "company": doc.company,
                "employee" : last_log.employee,
                "time_logs": [
                    {
                        "activity_type": last_log.get("activity_type"),
                        "from_time": last_log.get("from_time"),
                        "to_time": last_log.get("to_time"),
                        "project": doc.project,
                        "task": last_log.get("task")
                    }
                ]
            })

            timesheet_doc.flags.ignore_permissions = True
            timesheet_doc.insert()
            timesheet_doc.submit()

            # Append a new row for each employee with reference
            doc.append("custom_unproductive_work_timelogs", {
                "activity_type": last_log.get("activity_type"),
                "from_time": last_log.get("from_time"),
                "to_time": last_log.get("to_time"),
                "project": doc.project,
                "task": last_log.get("task"),
                "employee": emp,
                "reference": timesheet_doc.name
            })

        # Remove the original last row (because now we inserted employee-wise rows)
        doc.custom_unproductive_work_timelogs.remove(last_log)

    else:
        # No employees → Single timesheet (existing logic)

        timesheet_doc = frappe.get_doc({
            "doctype": "Timesheet",
            "parent_project": doc.project,
            "company": doc.company,
            "time_logs": [
                {
                    "activity_type": last_log.get("activity_type"),
                    "from_time": last_log.get("from_time"),
                    "to_time": last_log.get("to_time"),
                    "project": doc.project,
                    "task": last_log.get("task")
                }
            ]
        })
        timesheet_doc.flags.ignore_permissions = True
        timesheet_doc.insert()
        timesheet_doc.submit()

        last_log.reference = timesheet_doc.name

    doc.save()

    return {"status": "success"}

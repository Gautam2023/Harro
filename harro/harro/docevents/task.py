import frappe
import json
from frappe.utils import now
from frappe.desk.form.assign_to import add as add_assignment


def validate(self, method=None):
    if self.depends_on:
        for row in self.depends_on:
            if row.task and row.custom_expected_start_date and row.custom_expected_end_date:

                task_doc = frappe.get_doc("Task", row.task)

                # Update only if values are different
                if task_doc.exp_start_date != row.custom_expected_start_date:
                    task_doc.exp_start_date = row.custom_expected_start_date

                if task_doc.exp_end_date != row.custom_expected_end_date:
                    task_doc.exp_end_date = row.custom_expected_end_date

                if task_doc.expected_time != row.custom_expected_time:
                    task_doc.expected_time = row.custom_expected_time

                if row.custom_user not in task_doc._assign:
                    add_assignment({"doctype": self.doctype, "name": self.name, "assign_to": [row.custom_user]})
                task_doc.flags.ignore_permissions = True
                task_doc.save()


@frappe.whitelist()
def update_time_log(arg):
    args = json.loads(arg)
    if existing_task := frappe.db.exists("Task", {"custom_employee__assign_to_employee_" : args.get("employee"), "working_status" : "Work In Progress"}):
        arg = {
            "task" : existing_task,
            "to_time" : now()
        }
        update_stop_task_log(arg, start_new = True)
    doc = frappe.get_doc("Task", args.get("task"))
    doc.append("unproductive_work_timelogs", {
        "from_time" : args.get("from_time"),
        "activity_type" : args.get('activity_type'),
        "employee" : args.get("employee"),
        "project" : doc.project,
        "task" : args.get("task")
    })
    if not doc.custom_employee__assign_to_employee_:
        doc.custom_employee__assign_to_employee_ = args.get("employee")
    doc.flags.ignore_permissions=True
    doc.working_status = "Work In Progress"
    doc.save()
    return True

@frappe.whitelist()
def update_stop_task_log(arg, start_new=False):
    if not start_new:
        args = json.loads(arg)
    else:
        args = arg
    doc = frappe.get_doc("Task", args.get("task"))
    row = doc.unproductive_work_timelogs[-1]
    doc.unproductive_work_timelogs[-1].to_time = args.get("to_time")
    doc.flags.ignore_permissions = True
    doc.save()

    timesheet = frappe.db.get_value("Timesheet", {
                    "employee" : doc.custom_employee__assign_to_employee_,
                    "parent_project" : doc.project,
                    "docstatus" :  0
                } ,"name")
    if timesheet:
        timesheet_doc = frappe.get_doc("Timesheet", timesheet)
        timesheet_doc.append("time_logs", {
            "activity_type" : row.get("activity_type"),
            "from_time" : row.get("from_time"),
            "from_time" : row.get("to_time"),
            "employee" : row.get("employee"),
            "project" : row.get("project"),
            "task" : args.get("task")
        })
        timesheet_doc.flags.ignore_permissions=True
        timesheet_doc.save()
    else:
        frappe.get_doc({
            "doctype" : "Timesheet",
            "parent_project" : doc.project,
            "company" : doc.company,
            "employee" : row.get("employee"),
            "time_logs" : [
                {
                    "activity_type" : row.get("activity_type"),
                    "from_time" : row.get("from_time"),
                    "from_time" : row.get("to_time"),
                    "employee" : row.get("employee"),
                    "project" : row.get("project"),
                    "task" : args.get("task")
                }
            ]
        }).insert()
    frappe.db.set_value("Task",args.get("task"), "working_status", "On Hold")
    return True
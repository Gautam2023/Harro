import frappe
import json
from frappe.utils import now, get_datetime
from frappe.desk.form.assign_to import add as add_assignment


def validate(self, method=None):
    if not self.custom_actual_progress:
        self.custom_actual_progress = "#FFC067"
    if not self.is_new():
        update_task_details_of_parent_task(self)
    
    if not self.custom_assigned_to_responsible_user and self.custom_employee__assign_to_employee_:
        user = frappe.db.get_value("Employee", self.custom_employee__assign_to_employee_, "user_id")
        self.custom_assigned_to_responsible_user = user
    
    if not self.custom_employee__assign_to_employee_ and self.custom_assigned_to_responsible_user:
        if employee := frappe.db.exists("Employee", {"user_id" : self.custom_assigned_to_responsible_user}):
            self.custom_employee__assign_to_employee_ = employee

def update_task_details_of_parent_task(self):
    if self.depends_on:
        for row in self.depends_on:
            if not row.custom_employee and row.custom_user:
                if employee := frappe.db.exists("Employee", {"user_id" : row.custom_user}):
                    row.custom_employee = employee 

            if row.task:

                task_doc = frappe.get_doc("Task", row.task)

                # Update only if values are different
                if row.custom_expected_start_date and task_doc.exp_start_date != row.custom_expected_start_date:
                    frappe.db.set_value("Task", row.task, "exp_start_date", row.custom_expected_start_date)

                if row.custom_expected_end_date and task_doc.exp_end_date != row.custom_expected_end_date:
                    frappe.db.set_value("Task", row.task, "exp_end_date", row.custom_expected_end_date)

                if row.custom_expected_time and task_doc.expected_time != row.custom_expected_time:
                    frappe.db.set_value("Task", row.task, "expected_time", row.custom_expected_time)

                if not task_doc._assign:
                    _assign = []
                else:
                    _assign = eval(task_doc._assign)
                if row.custom_user and row.custom_user not in _assign:
                    add_assignment({"doctype": self.doctype, "name": row.task, "assign_to": [row.custom_user]})
                    frappe.db.set_value("Task", row.task, "custom_assigned_to_responsible_user", row.custom_user)
                    frappe.db.set_value("Task", row.task, "custom_employee__assign_to_employee_", row.custom_employee)
                else:
                    if not task_doc.custom_assigned_to_responsible_user and row.custom_user:
                        frappe.db.set_value("Task", row.task, "custom_assigned_to_responsible_user", row.custom_user)
                    if not task_doc.custom_employee__assign_to_employee_ and row.custom_employee:
                        frappe.db.set_value("Task", row.task, "custom_employee__assign_to_employee_", row.custom_employee)
    if self.custom_assigned_to_responsible_user:
        add_assignment({"doctype": self.doctype, "name": self.name, "assign_to": [self.custom_assigned_to_responsible_user]})



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
    if not row.get("to_time") or row.get("to_time") == '':
        row.update({
            "to_time" : args.get("to_time")
        })

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
            "to_time" : row.get("to_time"),
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
                    "to_time" : row.get("to_time"),
                    "employee" : row.get("employee"),
                    "project" : row.get("project"),
                    "task" : args.get("task")
                }
            ]
        }).insert()
    frappe.db.set_value("Task",args.get("task"), "working_status", "On Hold")
    return True

# Scheduler : Stop Timer after every 2 hours
def update_task_timer():
    task_list = frappe.db.get_list("Task", {"working_status" : 'Work In Progress'})
    for row in task_list:
        doc = frappe.get_doc("Task", row.name)
        if doc.unproductive_work_timelogs:
            from_time = get_datetime(doc.unproductive_work_timelogs[-1].from_time)
            current_time = get_datetime()
            diff_hours = (current_time - from_time).total_seconds() / 3600
            permissable_hours = frappe.db.get_single_value("Projects Settings", "task_cut_of_time")
            if diff_hours >= permissable_hours:
                doc.unproductive_work_timelogs[-1].to_time = now()
                doc.working_status = "On Hold"
                doc.flags.ignore_permissions = True
                doc.save()
                if doc.custom_employee__assign_to_employee_:
                    send_timer_stopper_notification(doc, permissable_hours)

def send_timer_stopper_notification(doc, permissible_hours):
    employee_name = frappe.db.get_value("Employee", doc.custom_employee__assign_to_employee_, "full_name")
    user_id = frappe.db.get_value("Employee", doc.custom_employee__assign_to_employee_, "user_id")
    if not user_id:
        return
    message = f"""
        <p>Hi {employee_name},</p>

        <p>You have exceeded the permissible working limit of <b>{permissible_hours} hours</b>. 
        If you are still working, please open the task below and restart the timer.</p>

        <p><b>Task:</b> {doc.name}</p>

        <p>Thank you,<br>
        Regards</p>

        <br><br>
        <center><small>This is a system-generated email. Please do not reply.</small></center>
    """

    subject = "Action Required: Please Restart Your Task Timer"
    frappe.sendmail(recipients=[user_id], subject=subject, message=message)

@frappe.whitelist()
def get_employee_id(user):
    if employee := frappe.db.exists("Employee", {"user_id" : user}):
        return employee
    else:
        None
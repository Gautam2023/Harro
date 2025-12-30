import frappe
from harro.harro.docevents.task import update_stop_task_log
from frappe.utils import today, now
import json

def after_insert(self, method=None):
    update_task_time_log_based_on_checkout(self)
    update_job_card_time_log(self)

def update_task_time_log_based_on_checkout(self):
    if self.log_type and self.log_type == "IN":
        return

    if not self.log_type:
        return
    
    employee = self.employee
    
    today_date = today()

    task_details = frappe.db.sql("""
        SELECT td.parent as name
        FROM `tabTimesheet Detail` as td
        Left Join `tabTask` as t ON td.parent = t.name        
        WHERE td.parenttype = 'Task'
        AND (td.to_time IS NULL OR td.to_time = '')
        AND DATE(td.from_time) = %s 
        AND t.custom_employee__assign_to_employee_ = %s
    """, (today_date, employee), as_dict=1)


    for row in task_details:
        arg = frappe._dict()
        arg.update({
            'task' : row.name,
            'to_time' : now()
         })
        
        update_stop_task_log(arg,start_new=True)


import frappe
from frappe.utils import today, now_datetime

def update_job_card_time_log(self):
    # Skip if IN or empty
    if not self.log_type or self.log_type == "IN":
        return

    employee = self.employee
    today_date = today()

    # Safe parameterized query (NO f-strings)
    jobcard_details = frappe.db.sql(
        """
        SELECT 
            jc.name AS job_card,
            jct_log.name AS time_log,
            jc.project
        FROM `tabJob Card Time Log` jct_log
        LEFT JOIN `tabJob Card` jc 
            ON jc.name = jct_log.parent
        WHERE 
            jct_log.employee = %(employee)s
            AND jc.docstatus = 0
            AND (jct_log.to_time IS NULL OR jct_log.to_time = '')
            AND DATE(jct_log.from_time) = %(date)s
        """,
        {"employee": employee, "date": today_date},
        as_dict=True
    )

    if not jobcard_details:
        return

    for row in jobcard_details:
        args = {
            "activity_type": "Check Out",
            "from_time": now_datetime(),
            "project": row.project,
        }

        update_unproductive_log_employee_wise(args, row.job_card, employee)

        args = {
			'job_card_id': row.job_card,
			"complete_time": now(),
			"status": "On Hold",
			"completed_qty": 0,
		}

        make_time_log(args)




def update_unproductive_log_employee_wise(args, job_card, employee):
    # args is already a dict — do NOT json.loads
    doc = frappe.get_doc("Job Card", job_card)

    doc.append(
        "custom_unproductive_work_timelogs",
        {
            "activity_type": args.get("activity_type"),
            "from_time": args.get("from_time"),
            "project": args.get("project"),
            "task": args.get("task") or "",
            "employee": employee,
        },
    )

    doc.flags.ignore_permissions = True
    doc.save()

    return {"status": "success"}


@frappe.whitelist()
def make_time_log(args):
	if isinstance(args, str):
		args = json.loads(args)

	args = frappe._dict(args)
	doc = frappe.get_doc("Job Card", args.job_card_id)
	doc.validate_sequence_id()
	doc.add_time_log(args)
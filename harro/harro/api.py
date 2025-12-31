import frappe
from frappe.utils import today, get_datetime, now_datetime, time_diff_in_seconds, now
from harro.harro.docevents.task import update_stop_task_log
from harro.harro.docevents.employee_checkin import update_unproductive_log_employee_wise, make_time_log

@frappe.whitelist()
def get_supplier_list(doctype, txt, searchfield, start, page_len, filters):
    filters = frappe._dict(filters)
    rfq_doc = frappe.get_doc("Request for Quotation", filters.get("name"))

    sq_supplier_list = frappe.db.sql(f"""
                                     Select sq.supplier
                                     From `tabSupplier Quotation` as sq
                                     Left Join `tabSupplier Quotation Item` as sqi ON sqi.parent = sq.name
                                     Where sq.docstatus < 2 and sqi.request_for_quotation = '{rfq_doc.name}'
                                """, as_dict=1)
    
    sq_supplier = [
        row.supplier for row in sq_supplier_list
    ]
    
    rfq_supplier_list = [
        row.supplier for row in rfq_doc.suppliers
    ]

    final_supplier_list = tuple([(s,) for s in rfq_supplier_list if s not in sq_supplier])

    return final_supplier_list



@frappe.whitelist()
def get_open_tasks_for_user():
    user = frappe.session.user

    # find task assigned to currently logged in user
    todos = frappe.db.get_all(
        "ToDo",
        filters = {
            "reference_type": "Task",
            "allocated_to": user,
            "status": "Open"
        },
        pluck = "reference_name"
    )

    if not todos:
        return {
            "value": 0,
            "fieldtype": "Int"
        }
    
    # count only valid tasks that are not completed/cancelled/template
    count = frappe.db.count(
        "Task",
        filters={
            "name": ["in",todos],
            "status": ["not in", ["Completed","Cancelled","Template"]]
        }
    )

    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "_assign": ["like", f"%{user}%"],
            "status": ["not in", ["Completed","Cancelled","Template"]]
        }
    }



def update_the_task_timer_based_on_shift_end():

    try:
        employees = frappe.get_all(
            "Employee",
            filters={"default_shift": ["!=", ""]},
            fields=["name", "default_shift"]
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Shift End Task Timer: Error fetching employees"
        )
        return

    if not employees:
        return

    for employee in employees:
        try:
            shift_end_time = frappe.db.get_value(
                "Shift Type",
                employee.default_shift,
                "end_time"
            )

            if not shift_end_time:
                continue

            shift_end_dt = get_datetime(f"{today()} {shift_end_time}")
            current_dt = now_datetime()
            diff_minutes = time_diff_in_seconds(shift_end_dt, current_dt) / 60

            # Only process tasks within -5 to 0 min of shift end
            if not (-5 <= diff_minutes <= 0):
                continue

            task_list = frappe.db.sql(
                """
                SELECT 
                    t.name AS task_name,
                    td.name AS timesheet_detail
                FROM `tabTask` t
                LEFT JOIN `tabTimesheet Detail` td 
                    ON td.parent = t.name
                WHERE 
                    t.status != 'Cancelled'
                    AND t.custom_employee__assign_to_employee_ = %(employee)s
                    AND (td.to_time IS NULL OR td.to_time = '')
                    AND td.creation < %(now)s
                """,
                {
                    "employee": employee.name,
                    "now": shift_end_dt
                },
                as_dict=True,
            )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Shift End Task Timer: Error pre-processing employee {employee.name}"
            )
            continue

        for row in task_list:
            try:
                arg = {
                    "task": row.task_name,
                    "to_time": now()
                }

                update_stop_task_log(arg, start_new=True)

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Shift End Task Timer: Error updating task {row.task_name} for employee {employee.name}"
                )


def update_the_job_card_timer_based_on_shift_end():

    try:
        employees = frappe.get_all(
            "Employee",
            filters={"default_shift": ["!=", ""]},
            fields=["name", "default_shift"]
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Shift End Job Card Timer: Error fetching employees"
        )
        return

    if not employees:
        return

    for emp in employees:
        try:
            shift_end_time = frappe.db.get_value(
                "Shift Type",
                emp.default_shift,
                "end_time"
            )

            if not shift_end_time:
                continue

            shift_end_dt = get_datetime(f"{today()} {shift_end_time}")
            current_dt = now_datetime()
            diff_minutes = time_diff_in_seconds(shift_end_dt, current_dt) / 60

            if not (-5 <= diff_minutes <= 0):
                continue

            job_card_list = frappe.db.sql(
                """
                SELECT 
                    jc.name AS job_card,
                    jc.project,
                    jct.name AS timesheet_detail
                FROM `tabJob Card` jc
                LEFT JOIN `tabJob Card Time Log` jct
                    ON jct.parent = jc.name
                WHERE 
                    jc.status = 'Work In Progress'
                    AND jct.employee = %(employee)s
                    AND (jct.to_time IS NULL OR jct.to_time = '')
                    AND jct.creation < %(now)s
                """,
                {
                    "employee": emp.name,
                    "now": shift_end_dt
                },
                as_dict=True,
            )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Shift End Job Card Timer: Error pre-processing employee {emp.name}"
            )
            continue

        for row in job_card_list:
            try:
                # Log unproductive entry
                args = {
                    "activity_type": "Shift End",
                    "from_time": now_datetime(),
                    "project": row.project,
                }
                update_unproductive_log_employee_wise(args, row.job_card, emp.name)

                # Stop time log
                args = {
                    'job_card_id': row.job_card,
                    "complete_time": now(),
                    "status": "On Hold",
                    "completed_qty": 0,
                }

                make_time_log(args)

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Shift End Job Card Timer: Error updating Job Card {row.job_card} for employee {emp.name}"
                )

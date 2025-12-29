import frappe
from harro.harro.docevents.task import update_stop_task_log
from frappe.utils import today, now

def after_insert(self, method=None):
    update_task_time_log_based_on_checkout(self)

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




    
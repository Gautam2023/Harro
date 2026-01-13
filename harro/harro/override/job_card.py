import frappe
from frappe.utils import (
	get_datetime,
	time_diff_in_seconds,
)
from erpnext.manufacturing.doctype.job_card.job_card import JobCard
import json

class CustomJobCard(JobCard):
    def add_time_log(self, args):
        last_row = []
        employees = args.employees
        if isinstance(employees, str):
            employees = json.loads(employees)

        if self.time_logs and len(self.time_logs) > 0:
            last_row = self.time_logs[-1]

        self.reset_timer_value(args)
        if last_row and args.get("complete_time"):
            for row in self.time_logs:
                if not row.to_time:
                    row.update(
                        {
                            "to_time": get_datetime(args.get("complete_time")),
                            "operation": args.get("sub_operation"),
                            "completed_qty": (args.get("completed_qty") if last_row.idx == row.idx else 0.0),
                        }
                    )
        elif args.get("start_time"):
            new_args = frappe._dict(
                {
                    "from_time": get_datetime(args.get("start_time")),
                    "operation": args.get("sub_operation"),
                    "completed_qty": 0.0,
                    "activity_type" : args.get("activity_type")
                }
            )

            if employees:
                for name in employees:
                    new_args.employee = name.get("employee")
                    self.add_start_time_log(new_args)
            else:
                self.add_start_time_log(new_args)

        if not self.employee and employees:
            self.set_employees(employees)

        if self.status == "On Hold":
            self.current_time = time_diff_in_seconds(last_row.to_time, last_row.from_time)

        self.save()
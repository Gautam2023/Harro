import frappe
from frappe.utils import getdate, date_diff

def execute():
    """
    Update extra_days for all Task records
    """

    tasks = frappe.get_all(
        "Task",
        fields=[
            "name",
            "exp_start_date",
            "exp_end_date",
            "act_start_date",
            "act_end_date"
        ]
    )

    for task in tasks:
        # Skip if any required date is missing
        if not (
            task.exp_start_date
            and task.exp_end_date
            and task.act_start_date
            and task.act_end_date
        ):
            continue

        expected_days = date_diff(
            getdate(task.exp_end_date),
            getdate(task.exp_start_date)
        )

        actual_days = date_diff(
            getdate(task.act_end_date),
            getdate(task.act_start_date)
        )

        extra_days = max(actual_days - expected_days, 0)

        frappe.db.set_value(
            "Task",
            task.name,
            "extra_days",
            extra_days,
            update_modified=False
        )

    frappe.db.commit()

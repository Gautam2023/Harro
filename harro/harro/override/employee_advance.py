import frappe
from frappe.utils import flt
from hrms.hr.doctype.expense_claim.expense_claim import get_expense_claim as original_get_expense_claim

@frappe.whitelist()
def get_expense_claim(employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount, return_amount):
    expense_claim = original_get_expense_claim(employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount, return_amount)

    advance_values = frappe.get_value(
        "Employee Advance",
        employee_advance_name,
        [
            "custom_ba_number",
            "custom_onward_travel_date",
            "custom_return_travel_date"
        ],
        as_dict = True
    )

    if advance_values:
        if advance_values.custom_ba_number:
            expense_claim.project = advance_values.custom_ba_number
        if advance_values.custom_onward_travel_date:
            expense_claim.custom_onward_travel_date = advance_values.custom_onward_travel_date
        if advance_values.custom_return_travel_date:
            expense_claim.custom_return_travel_date = advance_values.custom_return_travel_date

    return expense_claim
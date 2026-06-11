import frappe
from frappe.utils import getdate, add_days, add_months, get_last_day


def fix_due_date_based_on_posting_date(doc, method=None):
    use_posting_date = frappe.db.get_single_value(
        "Accounts Settings",
        "due_date_calculation_not_based_on_supplier_invoice_no"
    )

    if not use_posting_date:
        return

    base_date = getdate(doc.posting_date)

    # This skips validate_due_date() in validate_invoice_documents_schedule
    doc.ignore_default_payment_terms_template = 1

    # Recalculate payment_schedule manually from posting_date
    for schedule in doc.payment_schedule:
        if schedule.due_date_based_on == "Day(s) after invoice date":
            schedule.due_date = add_days(base_date, schedule.credit_days or 0)
        elif schedule.due_date_based_on == "Day(s) after the end of the invoice month":
            schedule.due_date = add_days(get_last_day(base_date), schedule.credit_days or 0)
        elif schedule.due_date_based_on == "Month(s) after the end of the invoice month":
            schedule.due_date = get_last_day(add_months(base_date, schedule.credit_months or 0))
        else:
            schedule.due_date = base_date

        if schedule.discount_validity_based_on == "Day(s) after invoice date":
            schedule.discount_date = add_days(base_date, schedule.discount_validity or 0)
        elif schedule.discount_validity_based_on == "Day(s) after the end of the invoice month":
            schedule.discount_date = add_days(get_last_day(base_date), schedule.discount_validity or 0)
        elif schedule.discount_validity_based_on == "Month(s) after the end of the invoice month":
            schedule.discount_date = get_last_day(add_months(base_date, schedule.discount_validity or 0))
        else:
            schedule.discount_date = base_date

    # Set doc level due_date from payment_schedule
    if doc.payment_schedule:
        doc.due_date = max(s.due_date for s in doc.payment_schedule)
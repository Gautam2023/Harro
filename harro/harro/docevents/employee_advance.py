import frappe

def set_per_day_allowance(doc, method=None):
    # Safety check
    if not doc.custom_country or not doc.custom_employment_type:
        return

    try:
        tlp = frappe.get_doc(
            "Travel Allowance Policy",
            "Travel Allowance Applicability Details Country Wise"
        )
    except frappe.DoesNotExistError:
        return

    for item in tlp.table_ntaw:
        if item.country == doc.custom_country:
            if doc.custom_employment_type == "Full-time":
                per_day = item.daily_allowance

            elif doc.custom_employment_type == "Probation":
                per_day = item.day_allowance
            else:
                return
            doc.custom_per_day_allowance = per_day or 0
            days = doc.custom_no_of_days or 0
            doc.custom_total_amount = days * (per_day or 0)
            doc.advance_amount = (days * (per_day or 0)) * 0.5

            break

import frappe

def set_per_day_allowance(doc, method=None):
    if not doc.custom_country:
        return

    if not doc.custom_employment_type:
        frappe.throw("Employment Type is required to calculate per day allowance.")

    try:
        tlp = frappe.get_doc(
            "Travel Allowance Policy",
            "Travel Allowance Applicability Details Country Wise"
        )
    except frappe.DoesNotExistError:
        frappe.throw("Travel Allowance Policy 'Travel Allowance Applicability Details Country Wise' not found.")

    per_day = 0

    for item in tlp.table_ntaw:
        if item.country != doc.custom_country:
            continue

        if doc.custom_country == "India":
            # Row selected by particulars, field selected by employment type
            if item.particulars != doc.custom_particulars:
                continue

            if doc.custom_employment_type == "Full-time":
                per_day = item.daily_allowance
            else:
                per_day = item.day_allowance

        else:
            # Non-India: single row per country, field selected by employment type
            if doc.custom_employment_type == "Full-time":
                per_day = item.daily_allowance
            else:
                per_day = item.day_allowance

        break

    doc.custom_per_day_allowance = per_day
    days = doc.custom_no_of_days or 0
    doc.custom_total_amount = days * per_day
    doc.advance_amount = doc.custom_total_amount * 0.5
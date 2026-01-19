import frappe

def on_employee_update(doc, method):
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    old_map = {row.name: row.number for row in old_doc.custom_visa_details}

    changed = []

    for row in doc.custom_visa_details:
        if row.name in old_map:
            if old_map[row.name] != row.number:
                changed.append((row.visa_country, old_map[row.name], row.number))

        if row.name not in old_map and row.number:
            changed.append((row.visa_country, None, row.number))

    if changed:
        email = None
        if doc.reports_to:
            email = frappe.db.get_value("Employee", doc.reports_to, "user_id")
            send_visa_change_mail(doc, email, changed)


def send_visa_change_mail(doc,email, changes):
    if not email:
        return
    ## employee being updated
    updated_employee_name = doc.employee_name or "Employee"
    # reporting to employee name
    reporting_to_name = frappe.db.get_value("Employee", doc.reports_to, "employee_name") or "Employee"
    rows = ""
    for c in changes:
        old_number = c[1] if c[1] else "—"
        rows += f"""
            <tr>
                <td style="padding: 6px 12px; border: 1px solid #ddd;">{c[0]}</td>
                <td style="padding: 6px 12px; border: 1px solid #ddd;">{old_number}</td>
                <td style="padding: 6px 12px; border: 1px solid #ddd;">{c[2]}</td>
            </tr>
        """

    html_message = f"""
        <p>Dear {reporting_to_name},</p>
        <p>The following Visa details have been updated for <b>{updated_employee_name}</b>:</p>

        <table style="border-collapse: collapse; font-size: 14px;">
            <tr style="background: #f5f5f5;">
                <th style="padding: 8px 12px; border: 1px solid #ccc; text-align:left;">Country</th>
                <th style="padding: 8px 12px; border: 1px solid #ccc; text-align:left;">Old Number</th>
                <th style="padding: 8px 12px; border: 1px solid #ccc; text-align:left;">New Number</th>
            </tr>
            {rows}
        </table>

        <p>If you believe this update is incorrect, please contact the HR/Travel Desk.</p>
        <br>
        <p>Best Regards,<br>HR Administration</p>
    """

    frappe.sendmail(
        recipients=[email],
        subject="Visa Details Updated",
        message=html_message
    )


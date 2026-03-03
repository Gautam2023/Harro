import frappe

def send_email_to_company_contact(doc, method):
    if not doc.custom_company_contact:
        return

    email_id = frappe.db.get_value(
        "Contact",
        doc.custom_company_contact,
        "user"
    )

    if not email_id:
        return

    purchase_orders = set()

    for ref in doc.references:

        if ref.reference_doctype == "Purchase Order":
            purchase_orders.add(ref.reference_name)

        elif ref.reference_doctype == "Purchase Invoice":
            po_list = frappe.get_all(
                "Purchase Invoice Item",
                filters={
                    "parent": ref.reference_name,
                    "purchase_order": ["is", "set"]
                },
                pluck="purchase_order"
            )

            for po in po_list:
                purchase_orders.add(po)

    po_list_str = ", ".join(purchase_orders) if purchase_orders else "N/A"

    frappe.sendmail(
        recipients=[email_id],
        subject=f"Payment Entry {doc.name} Submitted",
        message=f"""
        Dear {doc.custom_company_contact},<br><br>
        Payment Entry <b>{doc.name}</b> has been submitted.<br><br>
        Amount: {doc.paid_amount}<br>
        Linked Purchase Order(s): {po_list_str}<br><br>
        Regards,<br>
        {doc.owner}
        """
    )
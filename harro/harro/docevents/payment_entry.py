import frappe

def set_company_contact_from_pi(doc, method):
    for ref in doc.references:
        if ref.reference_doctype == "Purchase Invoice":
            company_contact = frappe.db.get_value(
                "Purchase Invoice",
                ref.reference_name,
                "custom_company_contact"
            )

            if company_contact:
                user = frappe.db.get_value(
                    "Contact",
                    company_contact,
                    "user"
                )

                if user:
                    doc.custom_company_contact = user

            break

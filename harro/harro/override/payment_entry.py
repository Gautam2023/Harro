import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_payment_entry as original_get_payment_entry
)

@frappe.whitelist()
def get_payment_entry(
    dt,
    dn,
    party_amount=None,
    bank_account=None,
    bank_amount=None,
    party_type=None,
    payment_type=None,
    reference_date=None,
    ignore_permissions=False,
    created_from_payment_request=False,
):

    pe = original_get_payment_entry(
        dt,
        dn,
        party_amount=party_amount,
        bank_account=bank_account,
        bank_amount=bank_amount,
        party_type=party_type,
        payment_type=payment_type,
        reference_date=reference_date,
        ignore_permissions=ignore_permissions,
        created_from_payment_request=created_from_payment_request,
    )

    # Directly map field
    pe.custom_company_contact = frappe.db.get_value(
        dt, dn, "custom_company_contact"
    )

    return pe
import frappe


def execute():
    """
    Patch entry point.
    Enqueue background job instead of blocking migrate.
    """
    frappe.enqueue(
        method=run_job,
        queue="long",
        timeout=6000,
        is_async=True,
    )


def run_job():
    """
    Background worker logic
    """

    po_list = frappe.get_all("Purchase Order", pluck="name")

    for po_name in po_list:
        try:
            doc = frappe.get_doc("Purchase Order", po_name)

            for row in doc.items:
                if not row.item_code:
                    continue

                description = frappe.db.get_value(
                    "Item",
                    row.item_code,
                    "description"
                )

                if description:
                    frappe.db.set_value(
                        row.doctype,
                        row.name,
                        "description",
                        description,
                        update_modified=False,
                    )


        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"PO Description Update Failed: {po_name}"
            )

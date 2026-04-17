import frappe
from frappe import _

@frappe.whitelist()
def cancel_stock_entry_in_rq(stock_entry):
    frappe.enqueue(
        cancel_stock_entry,
        stock_entry=stock_entry,
        queue="long",
        timeout=7200,
        job_name=f"cancel_stock_entry_{stock_entry}",  # ← prevents duplicate jobs
        deduplicate=True                                # ← Frappe will skip if already queued
    )
    return True

def cancel_stock_entry(stock_entry):
    lock_name = f"cancel_stock_entry_{stock_entry}"
    
    # Acquire a Redis-level distributed lock
    if not frappe.cache().set(lock_name, "locked", ex=300, nx=True):
        frappe.log_error(
            f"Stock Entry {stock_entry} cancellation already in progress. Skipping duplicate job.",
            "Cancel Stock Entry RQ"
        )
        return

    try:
        frappe.set_user("Administrator")

        # Re-check docstatus inside the lock
        doc = frappe.get_doc("Stock Entry", stock_entry)

        if doc.docstatus == 2:
            frappe.log_error(
                f"Stock Entry {stock_entry} is already cancelled",
                "Cancel Stock Entry RQ"
            )
            return

        if doc.docstatus != 1:
            frappe.log_error(
                f"Stock Entry {stock_entry} is not submitted (docstatus={doc.docstatus})",
                "Cancel Stock Entry RQ"
            )
            return

        doc.cancel()
        frappe.db.commit()
        frappe.logger().info(f"Stock Entry {stock_entry} cancelled successfully via RQ")

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), f"Failed to cancel Stock Entry {stock_entry}")
        raise e

    finally:
        # Always release the lock
        frappe.cache().delete(lock_name)
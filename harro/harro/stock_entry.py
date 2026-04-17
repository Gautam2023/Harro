import frappe
from frappe import _

@frappe.whitelist()
def cancel_stock_entry_in_rq(stock_entry):
    frappe.enqueue(
        cancel_stock_entry,
        stock_entry=stock_entry,
        queue="long",
        timeout=14400,  # bump to 4 hours for 5k rows
        job_id=f"cancel_stock_entry_{stock_entry}",
        deduplicate=True
    )
    return True


def cancel_stock_entry(stock_entry):
    lock_name = f"cancel_stock_entry_{stock_entry}"

    if not frappe.cache().set(lock_name, "locked", ex=14400, nx=True):
        frappe.log_error(
            f"Cancellation already in progress for {stock_entry}",
            "Cancel Stock Entry RQ"
        )
        return

    try:
        _do_cancel(stock_entry)
    finally:
        # Always release the lock
        frappe.cache().delete(lock_name)


def _do_cancel(stock_entry):
    frappe.db.max_rowcount = None  # remove any row limits

    doc = frappe.get_doc("Stock Entry", stock_entry)

    if doc.docstatus == 2:
        frappe.log_error(f"{stock_entry} already cancelled", "Cancel SE")
        return
    if doc.docstatus != 1:
        frappe.log_error(f"{stock_entry} not submitted", "Cancel SE")
        return

    # ── Step 1: Delete SLE in batches to avoid giant transaction ──────────
    frappe.log_error(f"Starting SLE cleanup for {stock_entry}", "Cancel SE Info")
    
    batch_size = 200
    while True:
        sle_names = frappe.get_all(
            "Stock Ledger Entry",
            filters={"voucher_type": "Stock Entry", "voucher_no": stock_entry},
            fields=["name"],
            limit=batch_size
        )
        if not sle_names:
            break
        for sle in sle_names:
            frappe.delete_doc("Stock Ledger Entry", sle.name, force=True, ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"Deleted {len(sle_names)} SLEs for {stock_entry}")

    # ── Step 2: Delete GL Entries in batches ───────────────────────────────
    frappe.log_error(f"Starting GLE cleanup for {stock_entry}", "Cancel SE Info")

    while True:
        gle_names = frappe.get_all(
            "GL Entry",
            filters={"voucher_type": "Stock Entry", "voucher_no": stock_entry},
            fields=["name"],
            limit=batch_size
        )
        if not gle_names:
            break
        for gle in gle_names:
            frappe.delete_doc("GL Entry", gle.name, force=True, ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"Deleted {len(gle_names)} GLEs for {stock_entry}")

    # ── Step 3: Repost bin qty for each item (in batches) ─────────────────
    frappe.log_error(f"Starting bin repost for {stock_entry}", "Cancel SE Info")

    items = frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": stock_entry},
        fields=["item_code", "s_warehouse", "t_warehouse"],
        limit=5000  # fetch all at once — just item codes, lightweight
    )

    warehouses_to_repost = set()
    for item in items:
        if item.s_warehouse:
            warehouses_to_repost.add((item.item_code, item.s_warehouse))
        if item.t_warehouse:
            warehouses_to_repost.add((item.item_code, item.t_warehouse))

    for item_code, warehouse in warehouses_to_repost:
        try:
            from erpnext.stock.utils import update_bin_qty
            update_bin_qty(item_code, warehouse, {})
            frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Bin repost failed: {item_code}/{warehouse}")

    # ── Step 4: Mark docstatus = 2 (Cancelled) ────────────────────────────
    frappe.db.set_value("Stock Entry", stock_entry, "docstatus", 2, update_modified=True)
    frappe.db.commit()

    frappe.log_error(f"Stock Entry {stock_entry} cancelled successfully", "Cancel SE Info")
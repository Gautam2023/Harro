import frappe
from frappe import _

@frappe.whitelist()
def cancel_stock_entry_in_rq(stock_entry):
    frappe.enqueue(
            cancel_stock_entry, 
            stock_entry=stock_entry, 
            queue="long", 
            timeout=7200
        )
    return True

def cancel_stock_entry(stock_entry):
    try:
        frappe.set_user("Administrator")
        doc = frappe.get_doc("Stock Entry", stock_entry)

        if doc.docstatus == 2:
            frappe.log_error(f"Stock Entry {stock_entry} is already cancelled", "Cancel Stock Entry RQ")
            return
        
        # Check if submitted
        if doc.docstatus != 1:
            frappe.log_error(f"Stock Entry {stock_entry} is not submitted (docstatus={doc.docstatus})", "Cancel Stock Entry RQ")
            return
        
        doc.cancel()
        frappe.db.commit()
        frappe.logger().info(f"Stock Entry {stock_entry} cancelled successfully via RQ")
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), f"Failed to cancel Stock Entry {stock_entry}")
        raise e

import frappe
from frappe import _

@frappe.whitelist()
def cancel_stock_entry_in_rq(stock_entry):
    frappe.enqueue(
            cancel_stock_entry, stock_entry=stock_entry, queue="long", timeout=7200
        )
    return True

def cancel_stock_entry(stock_entry):
    doc = frappe.get_doc("Stock Entry", stock_entry)
    doc.cancel()
import frappe
from frappe.utils import flt
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry as original_make_stock_entry

@frappe.whitelist()
def make_stock_entry(work_order_id, purpose, qty=None, target_warehouse=None):
    # original function call
    stock_entry_dict = original_make_stock_entry(work_order_id, purpose, qty, target_warehouse)
    
    # dict to document object
    stock_entry = frappe.get_doc(stock_entry_dict)
    
    # access project(BA Number) from work order
    work_order = frappe.get_doc("Work Order", work_order_id)
    
    # Map project to all items in the stock entry
    if work_order.get('project'):
        for item in stock_entry.items:
            item.project = work_order.project
    
    return stock_entry.as_dict()
import frappe
from erpnext.controllers.subcontracting_controller import make_rm_stock_entry as original

@frappe.whitelist()
def make_rm_stock_entry(subcontract_order, rm_items=None, order_doctype="Subcontracting Order", target_doc=None):
    # call original function
    stock_entry_dict = original(subcontract_order, rm_items, order_doctype, target_doc)

    # convert dict to doc so we can modify child items
    stock_entry = frappe.get_doc(stock_entry_dict)

    # get subcontracting order doc
    so = frappe.get_doc(order_doctype, subcontract_order)

    # map project field to all stock entry child tables
    if so.get("project"):
        for item in stock_entry.items:
            item.project = so.project
    return stock_entry.as_dict()
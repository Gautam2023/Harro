# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form
from erpnext.buying.doctype.purchase_order.purchase_order import is_po_fully_subcontracted

@frappe.whitelist()
def make_subcontracting_order(source_name, target_doc=None, save=False, submit=False, notify=False):
    if not is_po_fully_subcontracted(source_name):
        target_doc = get_mapped_subcontracting_order(source_name, target_doc)

        if (save or submit) and frappe.has_permission(target_doc.doctype, "create"):
            target_doc.save()

            if submit and frappe.has_permission(target_doc.doctype, "submit", target_doc):
                try:
                    target_doc.submit()
                except Exception as e:
                    target_doc.add_comment("Comment", _("Submit Action Failed") + "<br><br>" + str(e))

            if notify:
                frappe.msgprint(
                    _("Subcontracting Order {0} created.").format(
                        get_link_to_form(target_doc.doctype, target_doc.name)
                    ),
                    indicator="green",
                    alert=True,
                )

        return target_doc
    else:
        frappe.throw(_("This PO has been fully subcontracted."))
        

def get_mapped_subcontracting_order(source_name, target_doc=None):
    def post_process(source_doc, target_doc):
        # map project(BA Number) from purchase order to subcontracting order
        if source_doc.get('project'):
            target_doc.project = source_doc.project
            
        target_doc.populate_items_table()

        if target_doc.set_warehouse:
            for item in target_doc.items:
                item.warehouse = target_doc.set_warehouse
        else:
            if source_doc.set_warehouse:
                for item in target_doc.items:
                    item.warehouse = source_doc.set_warehouse
            else:
                for idx, item in enumerate(target_doc.items):
                    item.warehouse = source_doc.items[idx].warehouse
                    item.serial_no = source_doc.items[idx].serial_no

    if target_doc and isinstance(target_doc, str):
        target_doc = json.loads(target_doc)
        for key in ["service_items", "items", "supplied_items"]:
            if key in target_doc:
                del target_doc[key]
        target_doc = json.dumps(target_doc)

    target_doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Subcontracting Order",
                "field_map": {},
                "field_no_map": ["total_qty", "total", "net_total"],
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Purchase Order Item": {
                "doctype": "Subcontracting Order Service Item",
                "field_map": {
                    "name": "purchase_order_item",
                    "material_request": "material_request",
                    "material_request_item": "material_request_item",
                    "serial_no" :  "serial_no"
                },
                "field_no_map": ["qty", "fg_item_qty", "amount"],
                "condition": lambda item: item.qty != item.subcontracted_quantity,
            },
        },
        target_doc,
        post_process,
    )            

    return target_doc

def validate(self, method):
    for item in self.items:
        if self.is_subcontracted and frappe.db.get_value("Item", item.fg_item, "has_serial_no") and not item.serial_no:
            frappe.throw(f"Row {item.idx}: Update the serial no for item <b>{get_link_to_form('Item', item.fg_item)}<b>.")
        if not self.is_subcontracted and frappe.db.get_value('Item', item.item_code, 'has_serial_no') and not item.serial_no:
            frappe.throw(f"Row {item.idx}: Update the serial no for item <b>{get_link_to_form('Item', item.item_code)}<b>.")
        
            
            
        if item.serial_no:
            # Replace commas and newlines with spaces, then split
            serial_text = item.serial_no.replace(',', ' ').replace('\n', '   ')
            serial_list = [s.strip() for s in serial_text.split(' ') if s.strip()]
            serial_count = len(serial_list)

            if serial_count != item.qty:
                frappe.throw(
                    f"Row #{item.idx}: Quantity is {item.qty} but you entered {serial_count} serial numbers."
                )
    validate_material_request_qty(self, method)

@frappe.whitelist()
def get_company_contact():
	user = frappe.session.user
	user_id = frappe.db.exists("Contact", {"user": user})
	return user_id


def validate_material_request_qty(doc, method):
    if doc.items:
        for item in doc.items:
            if not item.material_request or not item.material_request_item:
                continue

            mr_item = frappe.get_doc("Material Request Item", item.material_request_item)

            if item.qty < mr_item.qty:
                frappe.throw(
                    _("Quantity mismatch for Item {0} in Material Request {1}. MR Qty: {2}, PO Qty: {3}").format(
                        item.item_code, item.material_request, mr_item.qty, item.qty
                    )
                )


def set_expected_delivery_date(doc, method=None):
    """
    Set expected_delivery_date on each item
    based on custom_expected_delivery_date in Purchase Order
    """

    if not doc.custom_expected_delivery_date:
        return

    for item in doc.items:
        item.expected_delivery_date = doc.custom_expected_delivery_date
import frappe
import json
from frappe import _
from frappe.utils import nowdate
from erpnext.manufacturing.doctype.work_order.work_order import make_work_order
from erpnext.stock.doctype.material_request.material_request import MaterialRequest


@frappe.whitelist()
def create_material_request(items):
    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw(_("No items selected"))

    # Create UNSAVED Material Request
    doc = frappe.new_doc("Material Request")
    doc.material_request_type = "Purchase"
    doc.schedule_date = nowdate()
    doc.company = frappe.defaults.get_user_default("Company")

    for item_code in items:
        purchase_uom = frappe.db.get_value("Item", item_code, "purchase_uom")
        stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
        uom = purchase_uom or stock_uom

        doc.append("items", {
            "item_code": item_code,
            "qty": 1,
            "uom": uom,
            "schedule_date": nowdate()
        })

    return doc.as_dict()



@frappe.whitelist()
def create_work_orders(items):
    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw("No items selected")

    item_code = items[0]

    bom_no = frappe.db.get_value(
        "BOM",
        {
            "item": item_code,
            "is_default": 1,
            "is_active": 1,
            "docstatus": 1
        },
        "name"
    )

    if not bom_no:
        frappe.throw(f"No Default BOM found for {item_code}")

    wo = make_work_order(
        bom_no=bom_no,
        item=item_code,
        qty=1,
        use_multi_level_bom=1
    )

    wo.company = frappe.defaults.get_user_default("Company")
    wo.planned_start_date = nowdate()

    return wo.as_dict()




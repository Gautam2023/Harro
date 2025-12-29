import frappe
import json
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_item_defaults
from frappe.utils import cint, cstr, flt, get_link_to_form, getdate, new_line_sep, nowdate


@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
    """Custom method to override standard make_purchase_order"""
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)

    def postprocess(source, target_doc):
        # Set project from custom_ba_number
        if source.custom_ba_number:
            target_doc.project = source.custom_ba_number
        
        if frappe.flags.args and frappe.flags.args.default_supplier:
            # items only for given default supplier
            supplier_items = []
            for d in target_doc.items:
                default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
                if frappe.flags.args.default_supplier == default_supplier:
                    supplier_items.append(d)
            target_doc.items = supplier_items

        from erpnext.stock.doctype.material_request.material_request import set_missing_values
        set_missing_values(source, target_doc)

    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        child_filter = d.name in filtered_items if filtered_items else True

        qty = d.ordered_qty or d.received_qty

        return qty < d.stock_qty and child_filter

    def update_item(obj, target, source_parent):
        target.conversion_factor = obj.conversion_factor

        qty = obj.ordered_qty or obj.received_qty
        target.qty = flt(flt(obj.stock_qty) - flt(qty)) / target.conversion_factor
        target.stock_qty = target.qty * target.conversion_factor
        if getdate(target.schedule_date) < getdate(nowdate()):
            target.schedule_date = None

    doclist = get_mapped_doc(
        "Material Request",
        source_name,
        {
            "Material Request": {
                "doctype": "Purchase Order",
                "validation": {"docstatus": ["=", 1], "material_request_type": ["=", "Purchase"]},
            },
            "Material Request Item": {
                "doctype": "Purchase Order Item",
                "field_map": [
                    ["name", "material_request_item"],
                    ["parent", "material_request"],
                    ["uom", "stock_uom"],
                    ["uom", "uom"],
                    ["sales_order", "sales_order"],
                    ["sales_order_item", "sales_order_item"],
                    ["wip_composite_asset", "wip_composite_asset"],
                    ["custom_ba_number", "project"], # BA Number field mapped 
                ],
                "postprocess": update_item,
                "condition": select_item,
            },
        },
        target_doc,
        postprocess,
    )

    doclist.set_onload("load_after_mapping", False)
    return doclist
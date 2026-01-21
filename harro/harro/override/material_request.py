import frappe
import json
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_item_defaults
from frappe.utils import cint, cstr, flt, get_link_to_form, getdate, new_line_sep, nowdate
from erpnext.stock.doctype.material_request.material_request import set_missing_values, update_item


@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)

    is_subcontracted = (
        frappe.db.get_value("Material Request", source_name, "material_request_type") == "Subcontracting"
    )

    def postprocess(source, target_doc):

        # changes start by fosserp
        # Set project from custom_ba_number
        if source.custom_ba_number:
            target_doc.project = source.custom_ba_number
        # changes end by fosserp
        
        target_doc.is_subcontracted = is_subcontracted
        if frappe.flags.args and frappe.flags.args.default_supplier:
            # items only for given default supplier
            supplier_items = []
            for d in target_doc.items:
                if is_subcontracted and not d.item_code:
                    continue
                default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
                if frappe.flags.args.default_supplier == default_supplier:
                    supplier_items.append(d)
            target_doc.items = supplier_items
        
        set_missing_values(source, target_doc)

    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        child_filter = d.name in filtered_items if filtered_items else True

        qty = d.ordered_qty or d.received_qty

        return qty < d.stock_qty and child_filter

    def generate_field_map():
        field_map = [
            ["name", "material_request_item"],
            ["parent", "material_request"],
            ["sales_order", "sales_order"],
            ["sales_order_item", "sales_order_item"],
            ["wip_composite_asset", "wip_composite_asset"],
            ["project", "project"]
        ]

        if is_subcontracted:
            field_map.extend([["item_code", "fg_item"], ["qty", "fg_item_qty"]])
        else:
            field_map.extend([["uom", "stock_uom"], ["uom", "uom"]])

        return field_map

    doclist = get_mapped_doc(
        "Material Request",
        source_name,
        {
            "Material Request": {
                "doctype": "Purchase Order",
                "validation": {
                    "docstatus": ["=", 1],
                    "material_request_type": ["in", ["Purchase", "Subcontracting"]],
                },
            },
            "Material Request Item": {
                "doctype": "Purchase Order Item",
                "field_map": generate_field_map(),
                "field_no_map": ["item_code", "item_name", "qty"] if is_subcontracted else [],
                "postprocess": update_item,
                "condition": select_item,
            },
        },
        target_doc,
        postprocess,
    )

    doclist.set_onload("load_after_mapping", False)
    return doclist
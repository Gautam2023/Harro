import frappe


def execute():
    po_list = frappe.db.get_list("Purchase Order", pluck="name")
    for row in po_list:
        doc = frappe.get_doc("Purchase Order", row)
        for d in doc.items:
            description = frappe.db.get_value("Item", d.item_code, "description")
            frappe.db.set_value(d.doctype, d.name, "description", description, update_modified=False)
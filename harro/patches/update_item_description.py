import frappe
from frappe.model.utils import get_fetch_values


def execute():
    items = frappe.get_all("Item", pluck="name")

    for item_name in items:
        item = frappe.get_doc("Item", item_name)
        description_html = build_description(item)

        if description_html:
            frappe.db.set_value(
                "Item",
                item.name,
                "description",
                description_html
            )



def build_description(item):
    for_description = [
        "Artikel Bez1",
        "Artikel Bez2",
        "Artikel Bez3",
        "Artikel Bez4",
    ]

    html = "<div>"

    for label in for_description:
        fieldname = make_fieldname(label)
        value = item.get(fieldname)

        if value:
            html += f"<p>{value}</p>"

    html += "</div>"

    return html


def make_fieldname(label):
    return label.strip().lower().replace(" ", "_")

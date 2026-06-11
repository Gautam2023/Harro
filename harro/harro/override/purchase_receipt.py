import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    make_purchase_invoice as original_make_purchase_invoice
)

class CustomPurchaseReceipt(PurchaseReceipt):
    def po_required(self):
        if frappe.db.get_value("Buying Settings", None, "po_required") == "Yes":
            for d in self.get("items"):
                is_allowed_without_po = frappe.db.get_value(
                    "Item",
                    d.item_code,
                    "is_allowed_without_po"
                )
                if is_allowed_without_po:
                    continue
                if not d.purchase_order:
                    frappe.throw(_("Purchase Order number required for Item {0}").format(d.item_code))

@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None, args=None):
    #original function call
    doclist = original_make_purchase_invoice(source_name, target_doc, args)

    pr = frappe.get_value(
        "Purchase Receipt",
        source_name,
        [
            "supplier_invoice_no",
            "supplier_invoice_date",
            "posting_date",
            "custom_customer_service",
            "goods_grn"
        ],
        as_dict=True
    )
    if pr:
        doclist.bill_no = pr.supplier_invoice_no
        doclist.bill_date = pr.supplier_invoice_date
        doclist.posting_date = pr.posting_date 

        # my custom field mapping
        doclist.custom_customer_service_ = pr.custom_customer_service
        doclist.from_goods_grn = pr.goods_grn

    return doclist
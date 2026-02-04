import frappe
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt

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
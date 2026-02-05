import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from frappe.utils import get_link_to_form
from frappe import throw, _

class CustomPurchaseInvoice(PurchaseInvoice):
    def po_required(self):
        if frappe.db.get_value("Buying Settings", None, "po_required") == "Yes":
            if frappe.get_value(
                "Supplier", self.supplier, "allow_purchase_invoice_creation_without_purchase_order"
            ):
                return

            for d in self.get("items"):
                is_allowed_without_po = frappe.db.get_value(
                    "Item",
                    d.item_code,
                    "is_allowed_without_po"
                )

                if is_allowed_without_po:
                    continue
                if not d.purchase_order:
                    msg = _("Purchase Order Required for item {}").format(frappe.bold(d.item_code))
                    msg += "<br><br>"
                    msg += _(
                        "To submit the invoice without purchase order please set {0} as {1} in {2}"
                    ).format(
                        frappe.bold(_("Purchase Order Required")),
                        frappe.bold(_("No")),
                        get_link_to_form("Buying Settings", "Buying Settings", "Buying Settings"),
                    )
                    throw(msg, title=_("Mandatory Purchase Order"))
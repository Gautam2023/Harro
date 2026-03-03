import frappe

def on_submit(self, method):

    if not self.has_batch_no:
        return

    # ======================================================
    # PURCHASE RECEIPT → update invoice, BOE & location fields in Batch
    # ======================================================
    if self.voucher_type == "Purchase Receipt":

        pr_item = frappe.db.get_value(
            "Purchase Receipt Item",
            self.voucher_detail_no,
            [
                "invoice_no",
                "bill_of_entry",
                "rack",
                "rejected_rack",
                "bin_location",
                "rejected_bin_location",
            ],
            as_dict=1,
        )

        update_data = {}
        if pr_item:
            if pr_item.get("invoice_no"):
                update_data["invoice_no"] = pr_item.get("invoice_no")
            if pr_item.get("bill_of_entry"):
                update_data["bill_of_entry"] = pr_item.get("bill_of_entry")

            # New rack / bin fields copied from Purchase Receipt Item to Batch
            for field in ["rack", "rejected_rack", "bin_location", "rejected_bin_location"]:
                if pr_item.get(field):
                    update_data[field] = pr_item.get(field)

        if update_data:
            _update_batches(self.entries, update_data)

        return

    # ======================================================
    # STOCK ENTRY BASED LOGIC
    # ======================================================
    if self.voucher_type == "Stock Entry":
        

        stock_entry_type = frappe.db.get_value(
            "Stock Entry",
            self.voucher_no,
            "stock_entry_type"
        )

        # ------------------------------------------------------
        # Material Receipt → update invoice, BOE & location fields in Batch
        # ------------------------------------------------------
        if stock_entry_type == "Material Receipt":

            se_item = frappe.db.get_value(
                "Stock Entry Detail",
                self.voucher_detail_no,
                [
                    "invoice_no",
                    "bill_of_entry",
                    "rack",
                    "rejected_rack",
                    "bin_location",
                    "rejected_bin_location",
                ],
                as_dict=1,
            )

            update_data = {}
            if se_item:
                if se_item.get("invoice_no"):
                    update_data["invoice_no"] = se_item.get("invoice_no")
                if se_item.get("bill_of_entry"):
                    update_data["bill_of_entry"] = se_item.get("bill_of_entry")

                for field in ["rack", "rejected_rack", "bin_location", "rejected_bin_location"]:
                    if se_item.get(field):
                        update_data[field] = se_item.get(field)

            if update_data:
                _update_batches(self.entries, update_data)

            return

        # ------------------------------------------------------
        # Manufacture & Repack → map RM batches into FG batch
        # ------------------------------------------------------
        if stock_entry_type in (
            "Material Transfer for Manufacture",
            "Repack",
            "Manufacture"
        ):

            _map_rm_batches_into_fg(self)



# =========================================================
# Helpers (clean & reusable)
# =========================================================

def _update_batches(entries, update_data):
    """Update Batch records linked in bundle entries with given field values."""
    for row in entries:
        if row.batch_no:
            frappe.db.set_value(
                "Batch",
                row.batch_no,
                update_data,
                update_modified=False
            )


def _map_rm_batches_into_fg(bundle_doc):

    stock_entry = frappe.get_doc(
        "Stock Entry",
        bundle_doc.voucher_no
    )

    rm_batches = set()

    # Collect all consumed RM batches
    for row in stock_entry.items:
        if row.s_warehouse and row.serial_and_batch_bundle:
            srb = frappe.get_doc(
                "Serial and Batch Bundle",
                row.serial_and_batch_bundle
            )

            for e in srb.entries:
                if e.batch_no:
                    rm_batches.add(e.batch_no)


    if not rm_batches:
        return

    # Push into FG batch RM Batch Details table
    for fg in bundle_doc.entries:
        if not fg.batch_no:
            continue

        batch_doc = frappe.get_doc("Batch", fg.batch_no)

        existing = {d.batch_no for d in batch_doc.rm_batch_details}

        for rm_batch in rm_batches:
            if rm_batch not in existing:
                batch_doc.append("rm_batch_details", {
                    "batch_no": rm_batch
                })

        batch_doc.save(ignore_permissions=True)


from frappe.utils import get_url_to_form

def email_notification(doc, method=None):
    if not doc.items:
        return

    items_data = []

    for row in doc.items:
        if not row.item_code:
            continue

        item_doc = frappe.get_cached_doc("Item", row.item_code)

        if item_doc.inspection_required_before_purchase:
            items_data.append({
                "item_code": row.item_code,
                "item_name": row.item_name,
                "qty": row.qty,
                "description" : row.description
            })

    if not items_data:
        return

    users = frappe.get_all(
        "Has Role",
        filters={"role": "QM Representative"},
        fields=["parent"]
    )

    email_list = []
    for user in users:
        email = frappe.db.get_value("User", user.parent, "email")
        if email:
            email_list.append(email)

    if not email_list:
        return

    rows = ""
    for item in items_data:
        rows += f"""
        <tr>
            <td style="padding:6px;border:1px solid #ddd;">{item['item_code']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{item['item_name']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{item['description']}</td>
            <td style="padding:6px;border:1px solid #ddd;text-align:right;">{item['qty']}</td>
        </tr>
        """

    doc_link = get_url_to_form(doc.doctype, doc.name)

    message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 13px;">
        <p>Dear QC Representative</p>
        <p>
            Purchase Receipt 
            <a href="{doc_link}"><b>{doc.name}</b></a> 
            contains list of items Require Quality Inspection.
        </p>

        <table style="border-collapse: collapse; margin-top:10px;">
            <tr style="background-color:#f2f2f2;">
                <th style="padding:6px;border:1px solid #ddd;">Item Code</th>
                <th style="padding:6px;border:1px solid #ddd;">Item Name</th>
                <th style="padding:6px;border:1px solid #ddd;">Description</th>
                <th style="padding:6px;border:1px solid #ddd;">Qty</th>
            </tr>
            {rows}
        </table>

        <p style="margin-top:15px;">
            Please perform Quality Inspection.
        </p>
        <p style="margin-top:15px;">
            <strong>
                Regards,<br>
                ERPNext
            </strong>
        </p>
    </body>
    </html>
    """

    frappe.sendmail(
        recipients=email_list,
        subject=f"Inspection Required: Purchase Receipt {doc.name}",
        message=message,
        reference_doctype=doc.doctype,
        reference_name=doc.name
    )

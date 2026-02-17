import frappe

def on_submit(self, method):

    if not self.has_batch_no:
        return

    # ======================================================
    # PURCHASE RECEIPT → update invoice & BOE in Batch
    # ======================================================
    if self.voucher_type == "Purchase Receipt":

        invoice_no, bill_of_entry = frappe.db.get_value(
            "Purchase Receipt Item",
            self.voucher_detail_no,
            ["invoice_no", "bill_of_entry"]
        )

        if invoice_no or bill_of_entry:
            _update_batches(self.entries, invoice_no, bill_of_entry)

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
        # Material Receipt → update invoice & BOE
        # ------------------------------------------------------
        if stock_entry_type == "Material Receipt":

            invoice_no, bill_of_entry = frappe.db.get_value(
                "Stock Entry Detail",
                self.voucher_detail_no,
                ["invoice_no", "bill_of_entry"]
            )

            if invoice_no or bill_of_entry:
                _update_batches(self.entries, invoice_no, bill_of_entry)

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

def _update_batches(entries, invoice_no, bill_of_entry):
    update_data = {
        "invoice_no": invoice_no,
        "bill_of_entry": bill_of_entry
    }

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


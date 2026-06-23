frappe.ui.form.on("Bank Statement Import", {

    process(frm) {
        if (!frm.doc.unprocessed_file) {
            frappe.msgprint({
                title: __("Missing File"),
                message: __("Please attach the unprocessed ICICI bank statement CSV first."),
                indicator: "red",
            });
            return;
        }
        if (!frm.doc.bank_account) {
            frappe.msgprint({
                title: __("Missing Bank Account"),
                message: __("Please select a Bank Account before processing."),
                indicator: "red",
            });
            return;
        }
        if (!frm.doc.currency) {
            frappe.msgprint({
                title: __("Missing Currency"),
                message: __("Please select a Currency before processing."),
                indicator: "red",
            });
            return;
        }

        // Don't rely on frm.save().then() — call directly
        // file_url is already committed to DB when the Attach field saved it
        frappe.call({
            method: "harro.harro.docevents.bank_statement_import.process_icici_bank_statement",
            args: {
                file_url    : frm.doc.unprocessed_file,
                bank_account: frm.doc.bank_account,
                currency    : frm.doc.currency,
                docname     : frm.doc.name,
            },
            freeze        : true,
            freeze_message: __("Converting ICICI bank statement to ERPNext format…"),
            callback(r) {
                if (r.message && r.message.status === "success") {
                    frappe.msgprint({
                        title    : __("Conversion Successful"),
                        message  : __(
                            `Bank statement converted successfully.<br>` +
                            `<b>${r.message.rows}</b> transactions imported` +
                            (r.message.skipped
                                ? `, <b>${r.message.skipped}</b> rows skipped.`
                                : ".")
                        ),
                        indicator: "green",
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title    : __("Conversion Failed"),
                        message  : (r.message && r.message.error)
                            ? r.message.error
                            : __("An unknown error occurred. Check the Error Log for details."),
                        indicator: "red",
                    });
                }
            },
        });
    },
});
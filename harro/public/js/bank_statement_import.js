// DocType : Bank Statement Import
// File    : harro/harro/public/js/bank_statement_import.js

frappe.ui.form.on("Bank Statement Import", {

    process(frm) {

        // ── Validation ────────────────────────────────────────────────────
        if (!frm.doc.unprocessed_file) {
            frappe.msgprint({
                title: __("Missing File"),
                message: __("Please attach the unprocessed ICICI bank statement first."),
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

        // ── Server call ───────────────────────────────────────────────────
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
                const res = r.message;

                // ── Hard failure ──────────────────────────────────────────
                if (!res || res.status !== "success") {
                    frappe.msgprint({
                        title    : __("Conversion Failed"),
                        message  : res && res.error
                            ? res.error
                            : __("An unknown error occurred. Check the Error Log for details."),
                        indicator: "red",
                    });
                    return;
                }

                // ── Build result dialog ───────────────────────────────────
                const total    = res.rows + res.skipped;
                const skipped  = res.skipped || 0;
                const imported = res.rows;

                // Summary line
                let html = `
                    <div style="margin-bottom:12px;">
                        <table style="width:100%;border-collapse:collapse;">
                            <tr>
                                <td style="padding:6px 12px 6px 0;color:#6c757d;">Total rows in file</td>
                                <td style="padding:6px 0;font-weight:600;">${total}</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 12px 6px 0;color:#6c757d;">Successfully converted</td>
                                <td style="padding:6px 0;font-weight:600;color:#28a745;">${imported}</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 12px 6px 0;color:#6c757d;">Skipped / errors</td>
                                <td style="padding:6px 0;font-weight:600;color:${skipped > 0 ? '#e74c3c' : '#28a745'};">${skipped}</td>
                            </tr>
                        </table>
                    </div>`;

                // Skipped rows detail table
                if (skipped > 0 && res.skipped_rows && res.skipped_rows.length) {
                    html += `
                        <details open>
                            <summary style="cursor:pointer;font-weight:600;color:#e74c3c;margin-bottom:8px;">
                                ▶ ${skipped} row(s) skipped — click to see details
                            </summary>
                            <div style="max-height:260px;overflow-y:auto;margin-top:8px;">
                                <table style="width:100%;border-collapse:collapse;font-size:12px;">
                                    <thead>
                                        <tr style="background:#f8f9fa;">
                                            <th style="padding:6px 8px;text-align:left;border-bottom:1px solid #dee2e6;white-space:nowrap;">Row #</th>
                                            <th style="padding:6px 8px;text-align:left;border-bottom:1px solid #dee2e6;">Reason</th>
                                            <th style="padding:6px 8px;text-align:left;border-bottom:1px solid #dee2e6;">Raw Data</th>
                                        </tr>
                                    </thead>
                                    <tbody>`;

                    res.skipped_rows.forEach((r, i) => {
                        const bg = i % 2 === 0 ? "#fff" : "#fafafa";
                        html += `
                                        <tr style="background:${bg};">
                                            <td style="padding:5px 8px;border-bottom:1px solid #f0f0f0;color:#6c757d;">${r.row}</td>
                                            <td style="padding:5px 8px;border-bottom:1px solid #f0f0f0;color:#e74c3c;">${frappe.utils.escape_html(r.reason)}</td>
                                            <td style="padding:5px 8px;border-bottom:1px solid #f0f0f0;font-family:monospace;color:#495057;font-size:11px;">${frappe.utils.escape_html(r.raw || "")}</td>
                                        </tr>`;
                    });

                    html += `
                                    </tbody>
                                </table>
                            </div>
                            <p style="margin-top:8px;font-size:12px;color:#6c757d;">
                                Full details are also logged in <b>Error Log</b> under the name
                                <i>ICICI Statement Skipped Rows — ${frm.doc.name}</i>
                            </p>
                        </details>`;
                }

                // Show dialog
                const indicator = skipped > 0 ? "orange" : "green";
                const title     = skipped > 0
                    ? __("Conversion Complete — {0} rows skipped", [skipped])
                    : __("Conversion Successful");

                frappe.msgprint({
                    title    : title,
                    message  : html,
                    indicator: indicator,
                    wide     : skipped > 0,   // wider dialog when there's a table
                });

                // Reload so import_file and preview section refresh
                frm.reload_doc();
            },
        });
    },
});
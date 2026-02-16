// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Planning", {
	refresh(frm) {
        if(!frm.is_new()){
            frm.add_custom_button(__("Purchase Invoice"), (frm)=>{
                frappe.model.open_mapped_doc({
                    method: "harro.harro.doctype.travel_planning.travel_planning.create_purchase_invoice",
                    frm: cur_frm,
                });
            }, __("Create"))

            frm.add_custom_button(__("Travel Checklist"), () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.create_travel_checklist",
                    args: { source_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __("Message"),
                                message: r.message,
                                indicator: "green"
                            });
                        }
                    }
                });
            }, __("Create"));
        }
	}
});

frappe.ui.form.on("Travel Planning Employee Details" , {
    travel_request(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.travel_request) return;

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.get_travel_dates",
            args: { travel_request: row.travel_request },
            callback: function(r) {
                if (!row.custom_onward_travel_date) {
                    frappe.model.set_value(cdt, cdn, "custom_onward_travel_date", r.message.custom_onward_travel_date);
                }
                if (!row.custom_return_travel_date) {
                    frappe.model.set_value(cdt, cdn, "custom_return_travel_date", r.message.custom_return_travel_date);
                }
            }
        });
    },

    custom_flight_booking_status(frm, cdt, cdn) {
        sync_booking_status(frm, cdt, cdn);
    },

    custom_hotel_booking_status(frm, cdt, cdn) {
        sync_booking_status(frm, cdt, cdn);
    }
});

function sync_booking_status(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    if (!row.travel_request) {
        console.log("Skipping sync: travel_request missing");
        return;
    }

    if (!row.travel_request_itinerary) {
        console.log("Skipping sync: travel_request_itinerary missing");
        return;
    }

    console.log("Syncing Travel Planning row to Travel Request:", row);

    frappe.call({
        method: "harro.harro.api.sync_booking_status_to_travel_request",
        args: {
            tp_child: row
        },
        callback: function(r) {
            console.log("Server response:", r);
            if (r.message && r.message.status === "success") {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: "green"
                });
            }
        }
    });
}

frappe.ui.form.on('Expense Details', {
    create_purchase_invoice: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.call({
            method: "harro.harro.api.get_purchase_invoice_defaults",
            args: {
                expense_detail_row: row,
                travel_doc: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    console.log(r.message);
                    frappe.set_route('Form', 'Purchase Invoice', r.message);
                }
            }
        });
    },
    send_email: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.email_sent) {
            frappe.msgprint("Email already sent for this row.");
            return;
        }

        frappe.call({
            method: "harro.harro.api.send_email",
            args: {
                expense_detail_row: row,
                travel_planning: frm.doc.name
            },
            callback: function(r) {
                if (!r.exc) {
                    frappe.msgprint("Email sent");

                    // Mark locally and refresh grid
                    row.email_sent = 1;
                    frm.refresh_field("expense_details");
                }
            }
        });
    }
});

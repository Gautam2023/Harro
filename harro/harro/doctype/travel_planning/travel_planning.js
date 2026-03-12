// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Planning", {
	refresh(frm) {
        set_profit_color(frm);
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
	},
    custom_total_income_from_customer: function(frm) {
        calculate_profit(frm);
    },
    custom_total_expense: function(frm) {
        calculate_profit(frm);
    },
    custom_total_unclaimable_expense: function(frm) {
        calculate_total_expense(frm)
    },
    custom_total_claimable_expense: function(frm) {
        calculate_total_expense(frm)
    }
});

function calculate_total_expense(frm) {
    let claimable = frm.doc.custom_total_claimable_expense;
    let unclaimable = frm.doc.custom_total_unclaimable_expense;
    let total_expense = claimable + unclaimable
    frm.set_value("custom_total_expense" ,total_expense)
}

function calculate_profit(frm) {

    let income = frm.doc.custom_total_income_from_customer || 0;
    let expense = frm.doc.custom_total_expense || 0;

    let profit = income - expense;

    frm.set_value("custom_profit", profit);
    set_profit_color(frm);
}

function set_profit_color(frm) {

    let profit = frm.doc.custom_profit || 0;

    if (!frm.fields_dict.custom_profit) return;

    if (profit > 0) {
        frm.fields_dict.custom_profit.$wrapper
            .find("input")
            .css({"color": "green", "font-weight": "bold"});
    } 
    else if (profit < 0) {
        frm.fields_dict.custom_profit.$wrapper
            .find("input")
            .css({"color": "red", "font-weight": "bold"});
    } 
    else {
        frm.fields_dict.custom_profit.$wrapper
            .find("input")
            .css({"color": "", "font-weight": ""});
    }
}

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
    custom_hotel_cost_per_day: function(frm, cdt, cdn) {
        calculate_total_hotel_charge(frm, cdt, cdn)
    },
    room_night: function(frm, cdt, cdn) {
        calculate_total_hotel_charge(frm, cdt, cdn)
    },
    custom_create_purchase_invoice_flight: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.call({
            method: "harro.harro.docevents.travel_planning.get_flight_purchase_invoice_defaults",
            args: {
                employee_row: row,
                travel_doc: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Purchase Invoice', r.message);
                }
            }
        });
    },

    custom_create_purchase_invoice_hotel: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.call({
            method: "harro.harro.docevents.travel_planning.get_hotel_purchase_invoice_defaults",
            args: {
                employee_row: row,
                travel_doc: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Purchase Invoice', r.message);
                }
            }
        });
    }
});

function calculate_total_hotel_charge(frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    let cost_per_day = row.custom_hotel_cost_per_day || 0;
    let nights = row.room_night || 0;
    let total_hotel_charge = cost_per_day * nights
    frappe.model.set_value(cdt, cdn, "custom_total_hotel_charge", total_hotel_charge);
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

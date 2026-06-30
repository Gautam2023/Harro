// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Planning", {
    setup: function(frm) {
        frm.set_query("custom_booked_by", "travel_itinerary", function() {
            return {
                query: "harro.harro.doctype.travel_planning.travel_planning.get_travel_managers"
            };
        });

        frm.set_query("custom_hotel_booked_by", "travel_itinerary", function() {
            return {
                query: "harro.harro.doctype.travel_planning.travel_planning.get_travel_managers"
            };
        });
    },
	refresh(frm) {
        set_profit_color(frm);

        // Allowed Roles
        const allowed_roles = [
            "Travel Manager",
            "Accounts Manager",
            "Accounts User"
        ];

        // Check if current user has any allowed role
        const has_permission = allowed_roles.some(role =>
            frappe.user.has_role(role)
        );

        if(!frm.is_new() && has_permission){
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

            frm.add_custom_button(__("Expense Claim"), () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.make_expense_claim",
                    args: {source_name: frm.doc.name},
                    callback: function(r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route("Form", r.message.doctype, r.message.name);
                        }
                    }
                });
            }, __("Create"));

            frm.add_custom_button(__("Timesheet"), () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.make_timesheet",
                    args: {source_name: frm.doc.name},
                    callback: function(r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route("Form", r.message.doctype, r.message.name);
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
        calculate_total_expense(frm);
    },
    custom_total_claimable_expense: function(frm) {
        calculate_total_expense(frm);
    },
    custom_total_income_from_customer: function(frm) {
        calculate_outstanding_claims(frm);
    },
    custom_total_claimable_expense: function(frm) {
        calculate_outstanding_claims(frm);
    }
});

function calculate_outstanding_claims(frm) {
    let total_claimable_expense = frm.doc.custom_total_claimable_expense;
    let total_income_from_customer = frm.doc.custom_total_income_from_customer;
    let outstanding = total_claimable_expense - total_income_from_customer
    frm.set_value("custom_outstanding_claims", outstanding);
}

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
            method: "harro.harro.doctype.travel_planning.travel_planning.get_flight_purchase_invoice_defaults",
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
    custom_send_email_flight: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.custom_flight_email_sent) {
            frappe.msgprint("Email already sent for this row.");
            return;
        }

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.custom_flight_email_sent",
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
    },

    custom_create_purchase_invoice_hotel: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.get_hotel_purchase_invoice_defaults",
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
    custom_send_email_hotel: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.custom_flight_email_sent) {
            frappe.msgprint("Email already sent for this row.");
            return;
        }

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.custom_send_email_hotel",
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
    },
    custom_create_purchase_invoice: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.get_taxi_purchase_invoice_defaults",
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
    custom_send_email: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.custom_email_sent) {
            frappe.msgprint("Email already sent for this row.");
            return;
        }

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.custom_send_email",
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
    },
    custom_seat_charges: function(frm, cdt, cdn) {
        calculate_total_flight_cost(frm, cdt, cdn);
    },
    baggage_coast: function(frm, cdt, cdn) {
        calculate_total_flight_cost(frm, cdt, cdn);
    },
    custom_onward_flight_cost_as_per_invoice: function(frm, cdt, cdn) {
        calculate_total_flight_cost(frm, cdt, cdn);
    },
    custom_return_flight_cost_as_per_invoice: function(frm, cdt, cdn) {
        calculate_total_flight_cost(frm, cdt, cdn);
    },
    custom_round_trip_cost_as_per_invoice: function(frm, cdt, cdn) {
        calculate_total_flight_cost(frm, cdt, cdn);
    },
    custom_send_revised_ticket: function(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        // ── Validate ─────────────────────────────────────────────
        if (!row.custom_rescheduled_flight_ticket) {
            frappe.msgprint({
                title: "Attachment Missing",
                message: "Please attach the Rescheduled Flight Ticket before sending.",
                indicator: "red"
            });
            return;
        }

        if (!row.custom_contact_email) {
            frappe.msgprint({
                title: "Email Missing",
                message: "Employee Contact Email is missing in this row.",
                indicator: "red"
            });
            return;
        }

        // ── Confirm ───────────────────────────────────────────────
        frappe.confirm(
            `Send rescheduled ticket emails for <b>${row.employee_name || "this employee"}</b>?`,
            () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.send_revised_ticket_email",
                    // ↑ Replace with your actual Python file dotted path
                    args: {
                        travel_planning_name: frm.doc.name,
                        itinerary_row_name: cdn,
                    },
                    freeze: true,
                    freeze_message: "Sending emails...",
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: "Emails sent to employee and requestor successfully.",
                                indicator: "green"
                            }, 5);
                        }
                    }
                });
            }
        );
    }
});

function calculate_total_flight_cost(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let onward_flight_cost = row.custom_onward_flight_cost_as_per_invoice || 0;
    let return_flight_cost = row.custom_return_flight_cost_as_per_invoice || 0;
    let set_charge = row.custom_seat_charges || 0;
    let baggage_cost = row.baggage_coast || 0;
    let round_trip_cost = row.custom_round_trip_cost_as_per_invoice || 0;

    let total_flight_cost = onward_flight_cost + return_flight_cost + set_charge + baggage_cost + round_trip_cost;
    frappe.model.set_value(cdt, cdn, "custom_total_flight_cost_as_per_invoice", total_flight_cost);
}

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

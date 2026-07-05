// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

const TRAVEL_SEGMENT_STATUS_CLASS = {
    "Booked": "tp-status-booked",
    "In progress": "tp-status-progress",
    "Cancelled": "tp-status-cancelled",
    "Rescheduled": "tp-status-rescheduled",
};

function inject_travel_segment_styles() {
    if (document.getElementById("tp-segment-styles")) return;
    const style = document.createElement("style");
    style.id = "tp-segment-styles";
    style.textContent = `
        :root {
            --tp-surface: #faf9f7;
            --tp-surface-alt: #f1efe9;
            --tp-border: #e3ddd0;
            --tp-ink: #2b2620;
            --tp-ink-muted: #6b6357;
            --tp-accent: #2f6f6b;
            --tp-accent-soft: #e4efee;
            --tp-status-progress: #b3782d;
            --tp-status-cancelled: #b23b3b;
            --tp-status-rescheduled: #7a5cc4;
        }
        .dark .tp-segment-block, [data-theme="dark"] .tp-segment-block {
            --tp-surface: #262320;
            --tp-surface-alt: #2e2b26;
            --tp-border: #3d3830;
            --tp-ink: #ece7de;
            --tp-ink-muted: #a89e8f;
            --tp-accent: #6bc2bb;
            --tp-accent-soft: #1f3634;
        }
        .tp-segment-block {
            width: 50%;
            min-width: 260px;
            margin: 10px 0 16px;
            font-family: inherit;
        }
        .tp-segment-heading {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--tp-ink-muted);
            margin-bottom: 6px;
        }
        .tp-segment-heading .tp-icon {
            width: 14px;
            height: 14px;
            flex: none;
            color: var(--tp-accent);
        }
        .tp-segment-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 8px;
        }
        .tp-segment-empty {
            font-size: 12px;
            color: var(--tp-ink-muted);
            padding: 8px 10px;
            background: var(--tp-surface-alt);
            border: 1px dashed var(--tp-border);
            border-radius: 6px;
        }
        .tp-stub {
            position: relative;
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--tp-surface);
            border: 1px solid var(--tp-border);
            border-radius: 6px;
            padding: 8px 10px 8px 12px;
            overflow: hidden;
        }
        .tp-stub::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--tp-accent);
        }
        .tp-stub.tp-status-progress::before { background: var(--tp-status-progress); }
        .tp-stub.tp-status-cancelled::before { background: var(--tp-status-cancelled); }
        .tp-stub.tp-status-rescheduled::before { background: var(--tp-status-rescheduled); }
        .tp-stub-body {
            flex: 1;
            min-width: 0;
        }
        .tp-stub-title {
            font-size: 12.5px;
            font-weight: 600;
            color: var(--tp-ink);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .tp-stub-meta {
            font-size: 11px;
            color: var(--tp-ink-muted);
            font-variant-numeric: tabular-nums;
            margin-top: 1px;
        }
        .tp-stub-actions {
            display: flex;
            gap: 5px;
            flex: none;
        }
        .tp-stub-actions button {
            border: 1px solid var(--tp-border);
            background: var(--tp-surface-alt);
            color: var(--tp-ink);
            width: 26px;
            height: 26px;
            border-radius: 5px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .tp-stub-actions button.tp-view,
        .tp-stub-actions button.tp-edit {
            color: var(--tp-accent);
            border-color: var(--tp-accent);
            background: var(--tp-accent-soft);
        }
        .tp-stub-actions button.tp-view:hover,
        .tp-stub-actions button.tp-edit:hover {
            background: var(--tp-accent);
            color: #fff;
        }
        .tp-stub-actions button.tp-danger {
            color: var(--tp-status-cancelled);
            border-color: var(--tp-status-cancelled);
            background: #f6dede;
        }
        .tp-stub-actions button.tp-danger:hover {
            background: var(--tp-status-cancelled);
            color: #fff;
        }
        [data-theme="dark"] .tp-stub-actions button.tp-danger,
        .dark .tp-stub-actions button.tp-danger {
            background: #3a2222;
        }
        .tp-stub-actions button:focus-visible {
            outline: 2px solid var(--tp-accent);
            outline-offset: 1px;
        }
        .tp-add-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11.5px;
            font-weight: 600;
            color: var(--tp-accent);
            background: var(--tp-accent-soft);
            border: 1px solid transparent;
            border-radius: 5px;
            padding: 5px 10px;
            cursor: pointer;
        }
        .tp-add-btn:hover {
            border-color: var(--tp-accent);
        }
    `;
    document.head.appendChild(style);
}

const TRAVEL_SEGMENT_ICONS = {
    "Travel Flight Details": '<svg class="tp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-1 .1-1.3.5l-.7.7c-.5.5-.3 1.2.3 1.5L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.1 6.1c.3.5 1 .7 1.5.3l.7-.7c.4-.3.6-.8.5-1.3Z"/></svg>',
    "Travel Hotel Booking": '<svg class="tp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21V9l9-6 9 6v12"/><path d="M9 21v-6h6v6"/><path d="M3 12h18"/></svg>',
    "Travel Taxi Details": '<svg class="tp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 17h14M5 17a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm14 0a2 2 0 1 0 4 0 2 2 0 0 0-4 0ZM3 17V9l2-4h14l2 4v8"/><path d="M5 9h14"/></svg>',
};

const ICON_VIEW = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/><circle cx="12" cy="12" r="3"/></svg>';
const ICON_EDIT = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>';
const ICON_DELETE = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';

const TRAVEL_SEGMENT_TYPES = [
    {
        doctype: "Travel Flight Details",
        html_field: "flight_segments_html",
        get_method: "harro.harro.doctype.travel_planning.travel_planning.get_flight_segments",
        add_label: __("Add Flight"),
        label_fn: (row) => `${row.custom_onward_travel_date || "—"} → ${row.custom_return_travel_date || "—"}`,
        meta_fn: (row) => row.custom_flight_booking_status || __("Draft"),
        anchor_field: "custom_flight_details",
        section_label: __("Flight Details"),
        legacy_fields: [
            "custom_flight_details", "custom_flight_booking_details", "custom_onward_travel_date",
            "custom_return_travel_date", "custom_return_travel_from", "custom_return_travel_to",
            "custom_direct_flight", "custom_connection_flight", "custom_country", "custom_city",
            "custom_layover_time", "custom_seat_charges", "custom_flight_bill", "custom_return_flight_ticket",
            "custom_onward_flight_cost", "custom_return_flight_cost", "custom_round_trip_cost",
            "custom_flight_booking_status", "custom_booked_by", "custom_flight_cancellation_details",
            "custom_reason_for_cancellation", "custom_flight_cancellation_charges", "custom_flight_refund_amount",
            "custom_flight_reschedule_details", "custom_revised_travel_date", "custom_revised_return_date",
            "custom_reason_for_rescheduling", "custom_flight_reschedule_charges", "custom_rescheduled_flight_ticket",
            "custom_send_revised_ticket", "custom_column_break_gi5iu", "custom_flight_invoice_details",
            "custom_flight_invoice_id", "custom_service_type", "custom_flight_booking_vendor",
            "custom_flight_invoice_attachment", "custom_return_flight_invoice_attachment",
            "custom_round_trip_cost_as_per_invoice", "custom_onward_flight_cost_as_per_invoice",
            "custom_return_flight_cost_as_per_invoice", "custom_total_flight_cost_as_per_invoice",
            "custom_flight_payment_status", "custom_paid_amount_flight", "custom_outstanding_amount_flight",
            "custom_create_purchase_invoice_flight", "custom_send_email_flight", "custom_flight_email_sent",
        ],
    },
    {
        doctype: "Travel Hotel Booking",
        html_field: "hotel_segments_html",
        get_method: "harro.harro.doctype.travel_planning.travel_planning.get_hotel_segments",
        add_label: __("Add Hotel"),
        label_fn: (row) => `${row.custom_hotel_name || __("Hotel")}`,
        meta_fn: (row) => `${row.check_in_date || "—"} → ${row.check_out_date || "—"}`,
        anchor_field: "custom_section_break_q45fn",
        section_label: __("Hotel Booking"),
        legacy_fields: [
            "custom_section_break_q45fn", "custom_hotel_booking_details", "custom_hotel_name", "custom_taxi_bill",
            "custom_hotel_booking_status", "custom_hotel_booked_by", "custom_hotel_cancellation_details",
            "custom_hotel_cancellation_charges", "custom_hotel_refund_amount", "custom_hotel_reschedule_details",
            "custom_hotel_reschedule_charges", "custom_hotel_preferences", "custom_laundry_facility",
            "custom_laundry_facility_remarks", "custom_discount_on_meal", "custom_meal_discount_remarks",
            "custom_airport_transport", "custom_airport_transport_remarks", "custom_break_fast", "custom_wifi",
            "custom_rescheduled_hotel_ticket_", "custom_column_break_9gose", "custom_hotel_invoice_details",
            "custom_hotel_invoice_id", "custom_hotel_booking_vendor_name", "custom_service_category",
            "custom_payment_terms_for_hotel_booking", "custom_hotel_cost_per_day", "custom_total_hotel_charge",
            "custom_total_hotel_charge_as_per_invoice", "custom_hotel_payment_status", "custom_paid_amount_hotel",
            "custom_outstanding_amount_hotel", "custom_create_purchase_invoice_hotel", "custom_send_email_hotel",
        ],
    },
    {
        doctype: "Travel Taxi Details",
        html_field: "taxi_segments_html",
        get_method: "harro.harro.doctype.travel_planning.travel_planning.get_taxi_segments",
        add_label: __("Add Taxi"),
        label_fn: (row) => `${row.custom_taxi_type || __("Taxi")}`,
        meta_fn: (row) => row.custom_driver_name ? __("Driver: {0}", [row.custom_driver_name]) : __("No driver assigned"),
        anchor_field: "custom_taxi_details",
        section_label: __("Taxi Details"),
        legacy_fields: [
            "custom_taxi_details", "custom_taxi_required", "custom_driver_contact_number", "custom_taxi_type",
            "custom_airport_transfer", "custom_daily_transfer", "custom_out_of_india", "custom_taxi_number",
            "custom_driver_name", "custom_taxi_invoice_attachment", "custom_column_break_d9krg",
            "custom_taxi_invoice_details", "custom_taxi_invoice_id", "custom_service_item", "custom_taxi_vendor",
            "custom_daily_transfer_taxi_cost", "custom_create_purchase_invoice", "custom_send_email",
        ],
    },
];

frappe.ui.form.on("Travel Planning", {
	refresh(frm) {
        set_profit_color(frm);
        render_all_segment_lists(frm);
        open_itinerary_row_from_route(frm);

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
    form_render(frm, cdt, cdn) {
        add_segment_buttons(frm, cdt, cdn);
    },
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

function add_segment_buttons(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const employee = row.custom_employee;

    const grid_row = frm.fields_dict.travel_itinerary.grid.grid_rows_by_docname[cdn];
    if (!grid_row || !grid_row.grid_form) return;

    // Hide the legacy flat custom_* fields for every segment type — the
    // Add/View/Edit/Delete flow below replaces them, including for segment 1.
    TRAVEL_SEGMENT_TYPES.forEach((segment_type) => {
        segment_type.legacy_fields.forEach((fieldname) => {
            const field = grid_row.grid_form.fields_dict[fieldname];
            if (field) {
                field.df.hidden = 1;
                field.refresh();
            }
        });
    });

    TRAVEL_SEGMENT_TYPES.forEach((segment_type) => {
        render_row_segment_section(frm, grid_row, segment_type, employee, cdn);
    });
}

function render_row_segment_section(frm, grid_row, segment_type, employee, cdn) {
    inject_travel_segment_styles();

    const anchor_field = grid_row.grid_form.fields_dict[segment_type.anchor_field];
    if (!anchor_field) return;

    // Section Break "fields" expose their DOM as `.wrapper`, not `.$wrapper` (which
    // is only set on regular value-holding controls) — use whichever is present.
    const $anchor_wrapper = anchor_field.$wrapper || anchor_field.wrapper;
    if (!$anchor_wrapper) return;

    const $container_class = `segment-section-${segment_type.doctype.replace(/\s+/g, "-")}`;
    $anchor_wrapper.siblings(`.${$container_class}`).remove();

    const $section = $(`
        <div class="tp-segment-block ${$container_class}">
            <div class="tp-segment-heading">
                ${TRAVEL_SEGMENT_ICONS[segment_type.doctype]}
                <span>${segment_type.section_label}</span>
            </div>
            <div class="tp-segment-list"></div>
        </div>
    `).insertAfter($anchor_wrapper);

    const $list = $section.find(".tp-segment-list");

    if (!employee) {
        $list.html(
            `<div class="tp-segment-empty">${__(
                "Select a Travel Request with an Employee to add Flight/Hotel/Taxi segments."
            )}</div>`
        );
        return;
    }

    $(`<button class="tp-add-btn">+ ${segment_type.add_label}</button>`)
        .on("click", () => open_new_segment(frm, segment_type, employee, cdn))
        .appendTo($section);

    frappe.call({
        method: segment_type.get_method,
        args: { travel_planning: frm.doc.name },
        callback: function (r) {
            const rows = (r.message || []).filter((seg) => seg.travel_itinerary_row === cdn);

            if (!rows.length) {
                $list.html(`<div class="tp-segment-empty">${__("No segments added yet.")}</div>`);
                return;
            }

            $list.empty();
            rows.forEach((seg_row) => {
                const status_class = TRAVEL_SEGMENT_STATUS_CLASS[seg_row.custom_flight_booking_status || seg_row.custom_hotel_booking_status] || "";
                const $stub = $(`
                    <div class="tp-stub ${status_class}">
                        <div class="tp-stub-body">
                            <div class="tp-stub-title">${frappe.utils.escape_html(segment_type.label_fn(seg_row))}</div>
                            <div class="tp-stub-meta">${__("Segment")} ${seg_row.segment_no || ""} · ${frappe.utils.escape_html(segment_type.meta_fn(seg_row))}</div>
                        </div>
                        <div class="tp-stub-actions">
                            <button class="tp-view" title="${__("View")}">${ICON_VIEW}</button>
                            <button class="tp-edit" title="${__("Edit")}">${ICON_EDIT}</button>
                            <button class="tp-delete tp-danger" title="${__("Delete")}">${ICON_DELETE}</button>
                        </div>
                    </div>
                `);

                $stub.find(".tp-view").on("click", () => view_segment(segment_type, seg_row));
                $stub.find(".tp-edit").on("click", () => edit_segment(frm, segment_type, seg_row));
                $stub.find(".tp-delete").on("click", () => delete_segment(frm, segment_type, seg_row));

                $list.append($stub);
            });
        },
    });
}

function open_new_segment(frm, segment_type, employee, cdn) {
    frappe.call({
        method: segment_type.get_method,
        args: { travel_planning: frm.doc.name },
        callback: function (r) {
            const existing = (r.message || []).filter((seg) => seg.travel_itinerary_row === cdn);
            const next_segment_no = existing.length
                ? Math.max(...existing.map((seg) => seg.segment_no || 0)) + 1
                : 1;

            frappe.route_options = { travel_planning: frm.doc.name };
            frappe.new_doc(segment_type.doctype, {
                travel_planning: frm.doc.name,
                employee: employee,
                travel_itinerary_row: cdn,
                segment_no: next_segment_no,
            });
        },
    });
}

function open_itinerary_row_from_route(frm) {
    if (!frappe.route_options || !frappe.route_options.open_itinerary_row) return;

    const cdn = frappe.route_options.open_itinerary_row;
    delete frappe.route_options.open_itinerary_row;

    const grid = frm.fields_dict.travel_itinerary.grid;
    const grid_row = grid.grid_rows_by_docname[cdn];
    if (grid_row) {
        grid_row.toggle_view(true);
    }
}

function render_all_segment_lists(frm) {
    if (frm.is_new()) return;
    TRAVEL_SEGMENT_TYPES.forEach((segment_type) => render_segment_list(frm, segment_type));
}

function render_segment_list(frm, segment_type) {
    inject_travel_segment_styles();

    frappe.call({
        method: segment_type.get_method,
        args: { travel_planning: frm.doc.name },
        callback: function (r) {
            const rows = r.message || [];
            const wrapper = frm.get_field(segment_type.html_field).$wrapper;
            wrapper.empty();

            const $block = $(`
                <div class="tp-segment-block">
                    <div class="tp-segment-heading">
                        ${TRAVEL_SEGMENT_ICONS[segment_type.doctype]}
                        <span>${segment_type.section_label} — ${__("All Employees")}</span>
                    </div>
                    <div class="tp-segment-list"></div>
                </div>
            `).appendTo(wrapper);
            const $list = $block.find(".tp-segment-list");

            if (!rows.length) {
                $list.html(`<div class="tp-segment-empty">${__("No segments added yet.")}</div>`);
                return;
            }

            rows.forEach((row) => {
                const status_class = TRAVEL_SEGMENT_STATUS_CLASS[row.custom_flight_booking_status || row.custom_hotel_booking_status] || "";
                const $stub = $(`
                    <div class="tp-stub ${status_class}">
                        <div class="tp-stub-body">
                            <div class="tp-stub-title">${frappe.utils.escape_html(row.employee_name || row.employee || "")} — ${frappe.utils.escape_html(segment_type.label_fn(row))}</div>
                            <div class="tp-stub-meta">${__("Segment")} ${row.segment_no || ""} · ${frappe.utils.escape_html(segment_type.meta_fn(row))}</div>
                        </div>
                        <div class="tp-stub-actions">
                            <button class="tp-view" title="${__("View")}">${ICON_VIEW}</button>
                            <button class="tp-edit" title="${__("Edit")}">${ICON_EDIT}</button>
                            <button class="tp-delete tp-danger" title="${__("Delete")}">${ICON_DELETE}</button>
                        </div>
                    </div>
                `);

                $stub.find(".tp-view").on("click", () => view_segment(segment_type, row));
                $stub.find(".tp-edit").on("click", () => edit_segment(frm, segment_type, row));
                $stub.find(".tp-delete").on("click", () => delete_segment(frm, segment_type, row));

                $list.append($stub);
            });
        },
    });
}

function view_segment(segment_type, row) {
    frappe.model.with_doctype(segment_type.doctype, () => {
        frappe.call({
            method: "frappe.client.get",
            args: { doctype: segment_type.doctype, name: row.name },
            callback: function (r) {
                const doc = r.message;
                if (!doc) return;

                const meta = frappe.get_meta(segment_type.doctype);
                const dialog = new frappe.ui.Dialog({
                    title: __("{0} — {1}", [segment_type.doctype, segment_type.label_fn(row)]),
                    size: "large",
                    fields: meta.fields
                        .filter((df) => !frappe.model.no_value_type.includes(df.fieldtype) || df.fieldtype === "Attach")
                        .map((df) => ({ ...df, read_only: 1 })),
                });
                dialog.set_values(doc);
                dialog.show();
            },
        });
    });
}

function edit_segment(frm, segment_type, row) {
    frappe.route_options = { travel_planning: frm.doc.name };
    frappe.set_route("Form", segment_type.doctype, row.name);
}

function delete_segment(frm, segment_type, row) {
    frappe.confirm(
        __("Delete this record?") + `<br><b>${frappe.utils.escape_html(segment_type.label_fn(row))}</b>`,
        () => {
            frappe.call({
                method: "harro.harro.doctype.travel_planning.travel_planning.delete_travel_segment",
                args: { doctype: segment_type.doctype, name: row.name },
                freeze: true,
                callback: function (r) {
                    if (!r.exc) {
                        frappe.show_alert({ message: __("Deleted"), indicator: "green" });
                        render_segment_list(frm, segment_type);
                        refresh_open_row_segment_sections(frm);
                    }
                },
            });
        }
    );
}

function refresh_open_row_segment_sections(frm) {
    const grid = frm.fields_dict.travel_itinerary.grid;
    Object.keys(grid.grid_rows_by_docname).forEach((cdn) => {
        const grid_row = grid.grid_rows_by_docname[cdn];
        if (grid_row && grid_row.grid_form && grid_row.grid_form.wrapper.is(":visible")) {
            add_segment_buttons(frm, "Travel Planning Employee Details", cdn);
        }
    });
}

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

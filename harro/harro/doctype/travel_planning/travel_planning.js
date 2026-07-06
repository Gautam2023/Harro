// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt


/**
 * Handles:
 *   1. "Add Traveller" grid button relabeling
 *   2. Auto-population of Travel Requestor on new documents
 *   3. Workflow interception for "Send to Travel Manager for Travel Plan
 *      Update" — validates Claim Status on all rows, then shows a
 *      read-only Review Confirmation dialog before applying the workflow
 *      action
 *   4. Claim Status mutual exclusivity on child table rows
 *   5. Visa status lookup + dialog when an Employee is set on a child row
 *      (International travel only), with Visa Request creation shortcut
 */


const TRAVEL_PLANNING = {
	CHILD_DOCTYPE: "Travel Planning Employee Details",
	GRID_FIELDNAME: "travel_itinerary",
	WORKFLOW_ACTION_REVIEW: "Send to Travel Manager for Travel Plan Update",
	CLAIM_STATUS_FIELDS: [
		"custom_harro_claim",
		"custom_customer_claim",
		"custom_no_claim",
		"custom_yet_to_decided",
	],
};

const VISA_DIALOG_CONFIG = {
	valid: {
		indicator: "green",
		status_text: "✔ Visa is Valid",
		color: "#28a745",
		bg: "#d4edda",
		show_action: false,
	},
	expired: {
		indicator: "orange",
		status_text: "✖ Visa Expired",
		color: "#c0392b",
		bg: "#f8d7da",
		show_action: true,
	},
	not_found: {
		indicator: "grey",
		status_text: "— No Visa Record Found",
		color: "#6c757d",
		bg: "#e2e3e5",
		show_action: true,
	},
};



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
    onload(frm) {
		relabel_add_traveller_button(frm);
	},
	refresh(frm) {
        relabel_add_traveller_button(frm);
		auto_set_travel_requestor(frm);
		bind_workflow_review_interception(frm);

        set_profit_color(frm);
        try_patch_grid_row_heading(frm);
        // Allowed Roles
        const allowed_roles = [
            "Travel Manager",
            "Accounts Manager",
            "Accounts User",
            "Employee"
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

            frm.add_custom_button(__("Employee Advance"), () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.make_employee_advance",
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

/**
 * Rename the grid's "Add Row" button to "Add Traveller".
 * Needs to run on both onload and refresh since the grid can be re-rendered.
 */
function relabel_add_traveller_button(frm) {
	const field = frm.get_field(TRAVEL_PLANNING.GRID_FIELDNAME);
	if (field?.grid?.wrapper) {
		field.grid.wrapper.find(".grid-add-row").text(__("Add Traveller"));
	}
}

/**
 * On a new document, default Travel Requestor to the Employee record
 * linked to the logged-in user.
 */
function auto_set_travel_requestor(frm) {
	if (!frm.is_new() || frm.doc.travel_requestor) return;

	frappe.db
		.get_value("Employee", { user_id: frappe.session.user }, "name")
		.then((r) => {
			if (r.message?.name) {
				frm.set_value("travel_requestor", r.message.name);
			}
		})
		.catch((err) => {
			console.error("Failed to auto-set Travel Requestor:", err);
		});
}

/**
 * Intercept the workflow action link click (mousedown, so it fires before
 * the dropdown's own click handling) for the "Send to Travel Manager for
 * Travel Plan Update" action. Re-bound on every refresh, so the previous
 * namespaced handler is removed first to avoid stacking duplicate handlers.
 */
function bind_workflow_review_interception(frm) {
	$(document).off("mousedown.tp_workflow");

	$(document).on(
		"mousedown.tp_workflow",
		"a.grey-link.dropdown-item",
		function (e) {
			const action = $(this).text().trim();
			if (action !== TRAVEL_PLANNING.WORKFLOW_ACTION_REVIEW) return;

			e.preventDefault();
			e.stopImmediatePropagation();
			e.stopPropagation();

			close_dropdown($(this));
			handle_send_to_travel_manager(frm, action);
		}
	);
}

function close_dropdown($link) {
	$link.closest(".dropdown").removeClass("show");
	$link.closest(".dropdown-menu").removeClass("show");
}

/**
 * Validate Claim Status on every itinerary row, then show the Review
 * Confirmation dialog. Blocks with an error message if any row is missing
 * a Claim Status selection.
 */
function handle_send_to_travel_manager(frm, action) {
	const invalid_rows = get_rows_missing_claim_status(frm);

	if (invalid_rows.length > 0) {
		frappe.msgprint({
			title: __("Claim Status Required"),
			indicator: "red",
			message: __(
				"Please select a Claim Status for traveller row(s) {0} before sending to the Travel Manager.",
				[invalid_rows.join(", ")]
			),
		});
		return;
	}

	show_review_confirmation_dialog(frm, action);
}

function get_rows_missing_claim_status(frm) {
	const invalid_rows = [];

	(frm.doc[TRAVEL_PLANNING.GRID_FIELDNAME] || []).forEach((row, idx) => {
		const selected = TRAVEL_PLANNING.CLAIM_STATUS_FIELDS.filter((f) => row[f]);
		if (selected.length === 0) {
			invalid_rows.push(idx + 1);
		}
	});

	return invalid_rows;
}

/**
 * Read-only summary dialog the user must confirm before the workflow
 * action is actually applied via frappe.xcall.
 */
function show_review_confirmation_dialog(frm, action) {
	const d = new frappe.ui.Dialog({
		title: __("Review Confirmation"),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", fieldname: "travel_summary" }],
		primary_action_label: __("Yes, Proceed"),
		primary_action() {
			d.hide();
			apply_workflow_action(frm, action);
		},
		secondary_action_label: __("No, Review Again"),
		secondary_action() {
			d.hide();
		},
	});

	d.fields_dict.travel_summary.$wrapper.html(build_review_html(frm));
	d.show();
}

function apply_workflow_action(frm, action) {
	frappe.xcall("frappe.model.workflow.apply_workflow", {
		doc: frm.doc,
		action: action,
	})
		.then((doc) => {
			frappe.model.sync(doc);
			frm.refresh();
		})
		.catch((err) => {
			frappe.msgprint({
				title: __("Workflow Action Failed"),
				indicator: "red",
				message: __("Could not apply the workflow action. Please try again."),
			});
			console.error("apply_workflow failed:", err);
		});
}

/**
 * Builds the HTML for the Review Confirmation dialog. All dynamic values
 * are HTML-escaped to avoid injecting markup via doc/child-table data.
 */
function build_review_html(frm) {
	const header_rows = [
		["Travel Type", frm.doc.travel_type, "Purpose of Travel", frm.doc.purpose_of_travel],
		["Customer", frm.doc.custom_customer, "Country", frm.doc.custom_country],
		["BA Number", frm.doc.ba_number, "HH Number", frm.doc.custom_hh_number],
	]
		.map(
			([l1, v1, l2, v2]) => `
				<tr>
					<td><b>${esc(l1)}</b></td>
					<td>${esc(v1) || "-"}</td>
					<td><b>${esc(l2)}</b></td>
					<td>${esc(v2) || "-"}</td>
				</tr>`
		)
		.join("");

	const traveller_columns = [
		"Sr", "Employee", "Employee HH ID", "Employee Name", "Status", "Contact Email",
		"Onward Travel Date", "Travel From", "Travel To", "Return Travel Date",
		"Return Travel From", "Return Travel To", "Flight Booking Status", "Stay Required",
		"Check-in Date", "Check-out Date", "Room Night", "Hotel Booking Status",
		"Taxi Required", "Pan-India Taxi", "Local Taxi", "Out of India",
	];

	const traveller_rows = (frm.doc[TRAVEL_PLANNING.GRID_FIELDNAME] || [])
		.map((row, idx) => build_traveller_row_html(row, idx))
		.join("");

	return `
		<style>
			.travel-review-table th,
			.travel-review-table td { vertical-align: top !important; }
			.travel-review-table th {
				text-align: left !important;
				white-space: nowrap;
				padding-top: 8px !important;
			}
			.travel-review-table td { white-space: nowrap; }
		</style>

		<div style="padding: 10px; max-height: 600px; overflow-y: auto;">
			<div class="alert alert-warning">
				<b>${__("Please verify all Travel Planning details before submission.")}</b>
			</div>

			<table class="table table-bordered">
				<tbody>${header_rows}</tbody>
			</table>

			<h4 style="margin-top:20px;">${__("Traveller Details")}</h4>

			<table class="table table-bordered table-sm travel-review-table">
				<thead>
					<tr>${traveller_columns.map((c) => `<th>${__(c)}</th>`).join("")}</tr>
				</thead>
				<tbody>${traveller_rows}</tbody>
			</table>

			<div style="margin-top:15px; padding:10px; background:#fff3cd; border:1px solid #ffeeba; border-radius:4px;">
				${__("Please review the above information carefully before sending it to the Travel Manager.")}
			</div>
		</div>`;
}


function build_traveller_row_html(row, idx) {
	const check = (val) => (val ? "✓" : "");

	const cells = [
		idx + 1,
		row.custom_employee || "-",
		row.employee_hh_id || "-",
		row.employee_name || "-",
		row.custom_status || "-",
		row.custom_contact_email || "-",
		row.custom_onward_travel_date || "-",
		row.travel_from || "-",
		row.travel_to || "-",
		row.custom_return_travel_date || "-",
		row.custom_return_travel_from || "-",
		row.custom_return_travel_to || "-",
		row.custom_flight_booking_status || "-",
	].map((v) => `<td>${esc(v)}</td>`);

	const checkbox_cells = [
		row.lodging_required,
	].map((v) => `<td style="text-align:center">${check(v)}</td>`);

	const dates_and_room = [
		row.check_in_date || "-",
		row.check_out_date || "-",
		row.room_night || 0,
		row.custom_hotel_booking_status || "-",
	].map((v) => `<td>${esc(v)}</td>`);

	const taxi_checkbox_cells = [
		row.custom_taxi_required,
		row.custom_airport_transfer,
		row.custom_daily_transfer,
		row.custom_out_of_india,
	].map((v) => `<td style="text-align:center">${check(v)}</td>`);

	return `<tr>${cells.join("")}${checkbox_cells.join("")}${dates_and_room.join("")}${taxi_checkbox_cells.join("")}</tr>`;
}

/** Minimal HTML-escaping helper for values interpolated into dialog markup. */
function esc(value) {
	if (value === undefined || value === null) return "";
	return String(value)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

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

        //  Validate
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

        // Confirm 
        frappe.confirm(
            `Send rescheduled ticket emails for <b>${row.employee_name || "this employee"}</b>?`,
            () => {
                frappe.call({
                    method: "harro.harro.doctype.travel_planning.travel_planning.send_revised_ticket_email",
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
    },
    travel_itinerary_add(frm) {
        try_patch_grid_row_heading(frm);
    },
    employee_name(frm, cdt, cdn) {
        refresh_open_row_heading(frm, cdn);
    },
    custom_employee(frm, cdt, cdn) {
        setTimeout(() => refresh_open_row_heading(frm, cdn), 300);
    },
    custom_harro_claim(frm, cdt, cdn) {
		enforce_exclusive_claim_status(frm, cdt, cdn, "custom_harro_claim");
	},
    custom_customer_claim(frm, cdt, cdn) {
		enforce_exclusive_claim_status(frm, cdt, cdn, "custom_customer_claim");
	},
	custom_no_claim(frm, cdt, cdn) {
		enforce_exclusive_claim_status(frm, cdt, cdn, "custom_no_claim");
	},
	custom_yet_to_decided(frm, cdt, cdn) {
		enforce_exclusive_claim_status(frm, cdt, cdn, "custom_yet_to_decided");
	},

	custom_employee(frm, cdt, cdn) {
		handle_employee_selected(frm, cdt, cdn);
	},
});

/**
 * Ensures only one of the four Claim Status checkboxes is set per row.
 * When `changed_field` is checked, all other claim status fields on the
 * same row are cleared.
 */
function enforce_exclusive_claim_status(frm, cdt, cdn, changed_field) {
	const row = locals[cdt][cdn];
	if (!row[changed_field]) return;

	TRAVEL_PLANNING.CLAIM_STATUS_FIELDS.forEach((field) => {
		if (field !== changed_field && row[field]) {
			frappe.model.set_value(cdt, cdn, field, 0);
		}
	});

	frm.refresh_field(TRAVEL_PLANNING.GRID_FIELDNAME);
}

/**
 * When an Employee is selected on an International travel row, look up
 * their visa records for the document's Country and show a status dialog.
 * No-op for non-International travel or incomplete rows.
 */
function handle_employee_selected(frm, cdt, cdn) {
	if (frm.doc.travel_type !== "International") return;

	const row = locals[cdt][cdn];
	const employee = row.custom_employee;
	const country = frm.doc.custom_country;
	if (!employee || !country) return;

	frappe.call({
		method: "frappe.client.get",
		args: { doctype: "Employee", name: employee },
		callback(r) {
			if (!r.message) return;
			const { emp, visa, case_type } = resolve_visa_status(r.message, country);
			show_visa_dialog(frm, emp, country, visa, case_type);
		},
		error(err) {
			frappe.msgprint({
				title: __("Lookup Failed"),
				indicator: "red",
				message: __("Could not fetch visa details for the selected employee."),
			});
			console.error("Employee visa lookup failed:", err);
		},
	});
}

/** Determines visa/valid/expired/not_found state for the given Employee + Country. */
function resolve_visa_status(emp, country) {
	const visa_details = emp.custom_visa_details || [];
	const today = frappe.datetime.get_today();

	const visa = visa_details.find(
		(v) => (v.visa_country || "").toLowerCase() === country.toLowerCase()
	);

	if (!visa) {
		return { emp, visa: null, case_type: "not_found" };
	}

	return { emp, visa, case_type: visa.to >= today ? "valid" : "expired" };
}

/**
 * Shows a read-only dialog summarizing visa status for an employee/country.
 * Offers a "Create Visa Request" shortcut for expired/missing visas.
 */
function show_visa_dialog(frm, emp, country, visa, case_type) {
	const config = VISA_DIALOG_CONFIG[case_type];

	const fields = [
		{ fieldtype: "Data", fieldname: "f_employee", label: __("Employee"), default: emp.employee_name, read_only: 1 },
		{ fieldtype: "Column Break" },
		{ fieldtype: "Data", fieldname: "f_country", label: __("Country"), default: country, read_only: 1 },
	];

	if (visa) {
		const date_label = case_type === "valid" ? __("Valid To") : __("Expired On");
		fields.push(
			{ fieldtype: "Section Break" },
			{ fieldtype: "Data", fieldname: "f_visa_number", label: __("Visa Number"), default: visa.number || "—", read_only: 1 },
			{ fieldtype: "Column Break" },
			{ fieldtype: "Date", fieldname: "f_visa_date", label: date_label, default: visa.to, read_only: 1 }
		);
	}

	fields.push(
		{ fieldtype: "Section Break" },
		{ fieldtype: "Data", fieldname: "f_status", label: __("Status"), default: config.status_text, read_only: 1 }
	);

	const dialog_opts = {
		title: __("Visa Status"),
		indicator: config.indicator,
		fields: fields,
	};

	if (config.show_action) {
		dialog_opts.primary_action_label = __("Create Visa Request");
		dialog_opts.primary_action = function () {
			d.hide();
			create_visa_request(frm, emp, country);
		};
		dialog_opts.secondary_action_label = __("Dismiss");
		dialog_opts.secondary_action = function () {
			d.hide();
		};
	} else {
		dialog_opts.primary_action_label = __("OK");
		dialog_opts.primary_action = function () {
			d.hide();
		};
	}

	const d = new frappe.ui.Dialog(dialog_opts);
	d.show();

	style_visa_status_field(d, config);
}

/**
 * Applies status colors to the read-only Status field. Uses a short
 * timeout since Frappe renders the read-only markup asynchronously
 * after `dialog.show()`.
 */
function style_visa_status_field(dialog, config) {
	setTimeout(() => {
		const $wrapper = dialog.fields_dict.f_status.$wrapper;
		const style = {
			color: config.color,
			"font-weight": "600",
			"background-color": config.bg,
			"border-color": config.color,
		};

		$wrapper.find("input").css({ ...style, "border-radius": "4px" });
		$wrapper
			.find('.like-disabled-input, .form-control[readonly], [data-fieldtype="Data"]')
			.css(style);
	}, 100);
}

function create_visa_request(frm, emp, country) {
	frappe.new_doc("Visa Request", {
		employee_id: emp.name,
		employee_name: emp.employee_name,
		visa_country: country,
		custom_travel_planning: frm.doc.name,
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

function try_patch_grid_row_heading(frm) {
    const grid = frm.fields_dict["travel_itinerary"]?.grid;
    if (!grid || !grid.grid_rows || !grid.grid_rows.length) return;

    const proto = Object.getPrototypeOf(grid.grid_rows[0]);
    if (proto.__employee_name_heading_patched) return;

    const original_show_form = proto.show_form;

    proto.show_form = function () {
        original_show_form.apply(this, arguments);
        if (this.grid.df.fieldname === "travel_itinerary") {
            const employee_name = this.doc.employee_name;
            this.grid_form.wrapper.find(".grid-form-heading .panel-title").html(employee_name || "");
        }
    };

    proto.__employee_name_heading_patched = true;
}

function refresh_open_row_heading(frm, cdn) {
    const grid = frm.fields_dict["travel_itinerary"]?.grid;
    if (!grid) return;
    const row = grid.grid_rows_by_docname[cdn];
    if (!row || !row.grid_form) return;

    const employee_name = row.doc.employee_name;
    row.grid_form.wrapper.find(".grid-form-heading .panel-title").html(employee_name || "");
}

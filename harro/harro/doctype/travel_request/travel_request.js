// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Request", {
	refresh(frm) {
        if (["Draft", "Trip Planned"].includes(frm.doc.workflow_state)) {
            frm.add_custom_button(__("Travel Planning"), function () {
                frappe.call({
                    method : "harro.harro.docevents.travel_planning.create_travel_plan",
                    args : {
                        names : [frm.doc.name]
                    }
                })
            },__("Create"));
        }
        set_employee_filter(frm);
	},
    custom_checkout_date_(frm) {
        calculate_nights_parent(frm);
    },
    custom_checkin_date(frm) {
        calculate_nights_parent(frm);
    }
});

function calculate_nights_parent(frm) {
    if (frm.doc.custom_checkin_date && frm.doc.custom_checkout_date_) {
        let check_in_date = frappe.datetime.str_to_obj(frm.doc.custom_checkin_date);
        let check_out_date = frappe.datetime.str_to_obj(frm.doc.custom_checkout_date_);

        let diff = frappe.datetime.get_diff(check_out_date, check_in_date);
        // number of nights (checkout - checkin)
        custom_room_night = diff > 0 ? diff : 0;
        console.log(custom_room_night);
        frm.set_value("custom_room_night", custom_room_night);
    }
}

function set_employee_filter(frm) {
    if (frm._employee_filter_set) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Employee',
            filters: { user_id: frappe.session.user },
            fieldname: 'name'
        },
        callback: function(response) {
            const logged_in_employee = response && response.message && response.message.name;

            if (!logged_in_employee) {
                frm.set_query('employee', function() {
                    return { filters: { name: ['in', []] } };
                });
                frm._employee_filter_set = true;
                setTimeout(() => {
                    frappe.msgprint({
                        title: __('Warning'),
                        message: __('No Employee record found for the logged-in user. You cannot create a Travel Request.'),
                        indicator: 'orange'
                    });
                }, 500);
                return;
            }

            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Employee',
                    filters: [
                        ['reports_to', '=', logged_in_employee],
                        ['status', '=', 'Active']
                    ],
                    fieldname: 'name',
                    limit: 0
                },
                callback: function(r) {
                    if (!r || r.exc) {
                        frappe.show_alert({
                            message: __('Failed to load employee list. Please refresh.'),
                            indicator: 'red'
                        });
                        return;
                    }

                    const direct_reports = (r.message || []).map(e => e.name);
                    const allowed = [logged_in_employee, ...direct_reports];

                    frm.set_query('employee', function() {
                        return {
                            filters: [
                                ['name', 'in', allowed],
                                ['status', '=', 'Active']
                            ]
                        };
                    });

                    frm.refresh_field('employee');
                    frm._employee_filter_set = true;
                }
            });
        }
    });
}

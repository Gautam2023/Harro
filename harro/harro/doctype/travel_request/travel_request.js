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
	},
    custom_checkout_date_(frm) {
        calculate_nights_parent(frm);
    },
    custom_checkin_date(frm) {
        calculate_nights_parent(frm);
    },
    onload: function(frm) {
        set_employee_filter(frm);
    },
    
    refresh: function(frm) {
        set_employee_filter(frm);
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
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Employee',
            filters: { user_id: frappe.session.user },
            fieldname: 'name'
        },
        callback: function(response) {
            if (response.message) {
                const logged_in_employee = response.message.name;

                frm.set_query('employee', function() {
                    return {
                        filters: {
                            reports_to: logged_in_employee,
                            status: 'Active'
                        }
                    };
                });
            } else {
                frm.set_query('employee', function() {
                    return {
                        filters: {
                            name: '' 
                        }
                    };
                });
                frappe.msgprint(__('No Employee record found for the logged-in user.'));
            }
        }
    });
}

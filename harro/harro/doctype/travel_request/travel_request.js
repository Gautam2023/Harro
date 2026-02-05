// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Request", {
	refresh(frm) {
        if(frm.doc.workflow_state == "Trip Planned"){
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

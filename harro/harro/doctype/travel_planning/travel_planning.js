// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Planning", {
	refresh(frm) {
        toggle_attach_fields(frm);
        if(!frm.is_new()){
            frm.add_custom_button(__("Purchase Invoice"), (frm)=>{
                frappe.model.open_mapped_doc({
                    method: "harro.harro.doctype.travel_planning.travel_planning.create_purchase_invoice",
                    frm: cur_frm,
                });
            }, __("Create"))
        }
	},
    travel_type(frm) {
        toggle_attach_fields(frm);
    }
});

function toggle_attach_fields(frm) {
    const is_international = frm.doc.travel_type === "International";
    frm.fields_dict.travel_itinerary.grid.toggle_display(
        "custom_travel_insurance",
        is_international
    );

    frm.fields_dict.travel_itinerary.grid.toggle_display(
        "custom_evisa",
        is_international
    )
}

frappe.ui.form.on("Travel Planning Employee Details" , {
    travel_request(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.travel_request) return;

        frappe.call({
            method: "harro.harro.doctype.travel_planning.travel_planning.get_travel_dates",
            args: {
                travel_request: row.travel_request
            },
            callback: function(r) {
                if (!row.custom_onward_travel_date) {
                    frappe.model.set_value(cdt, cdn, "custom_onward_travel_date", r.message.custom_onward_travel_date);
                }
                if (!row.custom_return_travel_date) {
                    frappe.model.set_value(cdt, cdn, "custom_return_travel_date", r.message.custom_return_travel_date);
                }
            }
        })
    }
});
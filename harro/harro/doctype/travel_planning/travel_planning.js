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
        }
	},
});

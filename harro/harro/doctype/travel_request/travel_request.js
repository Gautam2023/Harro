// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Request", {
	refresh(frm) {
        if(frm.doc.docstatus == 1){
            frm.add_custom_button(__("Travel Request"), function () {
                frappe.call({
                    method : "harro.harro.docevents.travel_planning.create_travel_plan",
                    args : {
                        names : [frm.doc.name]
                    }
                })
			},__("Create"));
        }
	},
});

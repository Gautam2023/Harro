// Copyright (c) 2025, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Taxi", {
	refresh(frm) {
        if (!frm.is_new()) {
            if (frm.doc.workflow_state === "Waiting for Payment") {
                frm.add_custom_button(__("Purchase Invoice"), (frm)=>{
                frappe.model.open_mapped_doc({
                    method: "harro.harro.doctype.taxi.taxi.create_purchase_invoice",
                    frm: cur_frm,
                });
            }, __("Create"))
            }
        }
	},
});

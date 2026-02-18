// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Travel Insurance Application Details', {
	refresh(frm) {
		console.log("Hello Ji kaise ho");

		if (!frm.is_new() && frm.doc.workflow_state === "Waiting for Payment") {
			frm.add_custom_button(
				__("Purchase Invoice"),
				function () {
					frappe.model.open_mapped_doc({
						method: "harro.harro.doctype.travel_insurance_application_details.travel_insurance_application_details.create_purchase_invoice",
						frm: frm
					});
				},
				__("Create")
			);
		}
	}
});


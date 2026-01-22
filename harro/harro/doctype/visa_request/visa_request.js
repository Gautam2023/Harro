// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visa Request", {
	refresh(frm) {
        frm.set_query("visa_checklist", function(doc){
            return {
                filters: {
					counrty: doc.visa_country,
				},
            }
        })
	},
    visa_country(frm) {
        if (!frm.doc.visa_country) return;

        frappe.db.get_value(
            'Country Wise visa Document Checklist',
            { country: frm.doc.visa_country },
            'name'
        ).then(r => {
            if (r.message) {
                console.log(r.message)
                frm.set_value('visa_checklist', r.message.name);
            } else {
                frm.set_value('visa_checklist', null);
                frappe.msgprint(__('No checklist found for selected country'));
            }
        });
    }
});

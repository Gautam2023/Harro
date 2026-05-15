// Copyright (c) 2026, Fosserp and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visa Request", {
	refresh(frm) {
        if (!frm.is_new() && frm.doc.workflow_state === "Waiting for Payment") {
            frm.add_custom_button(__("Purchase Invoice"), (frm) => {
                frappe.model.open_mapped_doc({
                    method: "harro.harro.doctype.visa_request.visa_request.create_purchase_invoice",
                    frm: cur_frm
                });
            }, __("Create"))
        }
        frm.set_query("visa_checklist", function(doc){
            return {
                filters: {
					country: doc.visa_country,
				},
            }
        })
        set_employee_filter(frm);
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
    },
    visa_checklist:(frm)=>{
        if (frm.doc.visa_checklist){
            frappe.call({
                method : "harro.harro.doctype.visa_request.visa_request.get_visa_check_list_details",
                args : {
                    chekck_list : frm.doc.visa_checklist
                },
                callback:(r)=>{
                    if(r.message){
                        frm.doc.check_list = []
                        r.message.checklist.forEach(e => {
                           let row = frm.add_child("check_list"); 
                           row.catogory = e.catogory
                           row.checklistname_of_document = e.checklistname_of_document
                           row.options = e.options
                        });
                        frm.refresh_field("check_list")
                    }
                }
            })
        }
    }
});


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
                frm.set_query('employee_id', function() {
                    return { filters: { name: ['in', []] } };
                });
                frm._employee_filter_set = true;
                setTimeout(() => {
                    frappe.msgprint({
                        title: __('Warning'),
                        message: __('No Employee record found for the logged-in user. You cannot create a Visa Request.'),
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

                    frm.set_query('employee_id', function() {
                        return {
                            filters: [
                                ['name', 'in', allowed],
                                ['status', '=', 'Active']
                            ]
                        };
                    });

                    frm.refresh_field('employee_id');
                    frm._employee_filter_set = true;
                }
            });
        }
    });
}

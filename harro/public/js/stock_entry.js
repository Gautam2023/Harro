frappe.ui.form.on("Stock Entry", {
    refresh: function (frm) {
        frm.set_query("bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rack){
                frappe.throw("Source Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.rack },
            };
        })
        frm.set_query("to_bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rack){
                frappe.throw("Target Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.to_rack },
            };
        })
        
        // Add button to submit in background
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.add_custom_button(__("Submit in Background"), function() {
                submit_stock_entry_in_background(frm);
            }, __("Actions"));
        }
	},
    project : (frm)=>{
        if(frm.doc.project){
            frm.doc.items.forEach(e => {
                frappe.model.set_value(e.doctype, e.name, "project", frm.doc.project)
            });
        }
    },
    items_on_form_rendered(frm){
        
    }
})

frappe.ui.form.on('Stock Entry Detail', {
    refresh:function(){
        console.log("hhhhh")
    },
    rack:function(frm, cdt, cdn){
        frm.set_query("bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rack){
                frappe.throw("Source Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.rack },
            };
        })
    },
    to_rack:function(frm, cdt, cdn){
        frm.set_query("to_bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rack){
                frappe.throw("Target Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.to_rack },
            };
        })
    }
});

// Function to submit Stock Entry in background via API
function submit_stock_entry_in_background(frm) {
    if (frm.doc.docstatus !== 0) {
        frappe.msgprint(__("Document is already submitted or cancelled."));
        return;
    }
    
    frappe.confirm(
        __("Are you sure you want to submit this Stock Entry in the background?"),
        function() {
            // Show loading indicator
            frappe.show_alert({
                message: __("Submitting Stock Entry in background..."),
                indicator: "blue"
            });
            
            frappe.call({
                method: "harro.harro.api.submit_stock_entry_in_background",
                args: {
                    stock_entry_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.show_alert({
                            message: __("Error submitting document. Please check Error Log."),
                            indicator: "red"
                        });
                    } else if (r.message) {
                        frappe.show_alert({
                            message: __("Stock Entry submission queued successfully! It will be processed in the background."),
                            indicator: "green"
                        });
                        // Reload the form after a short delay to check status
                        setTimeout(function() {
                            frm.reload_doc();
                        }, 2000);
                    }
                },
                error: function(r) {
                    frappe.show_alert({
                        message: __("Failed to submit Stock Entry. Please try again."),
                        indicator: "red"
                    });
                }
            });
        }
    );
}

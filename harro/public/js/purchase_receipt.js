frappe.ui.form.on("Purchase Receipt", {
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
        frm.set_query("rejected_bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rejected_rack){
                frappe.throw("Rejected Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.rejected_rack },
            };
        })
	},
    cost_center : (frm)=>{
        if(frm.doc.cost_center){
            frm.doc.items.forEach(e => {
                frappe.model.set_value(e.doctype, e.name, "cost_center", frm.doc.cost_center)
            });
        }
    },
    project : (frm)=>{
        if(frm.doc.project){
            frm.doc.items.forEach(e => {
                frappe.model.set_value(e.doctype, e.name, "project", frm.doc.project)
            });
        }
    }
})

frappe.ui.form.on('Purchase Receipt Item', {
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
    rejected_rack:function(frm, cdt, cdn){
        frm.set_query("rejected_bin_location", "items", function(doc, cdt, cdn){
            let d = locals[cdt][cdn]
            if(!d.rejected_rack){
                frappe.throw("Rejected Rack is not selected")
            }
            return {
                query: "harro.harro.docevents.stock_entry.get_bin_location",
                filters: { rack : d.rejected_rack },
            };
        })
    }
});

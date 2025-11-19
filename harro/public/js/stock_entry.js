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

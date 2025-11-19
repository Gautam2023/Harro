frappe.ui.form.on("Purchase Order Order", {
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
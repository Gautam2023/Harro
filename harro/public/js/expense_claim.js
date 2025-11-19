frappe.ui.form.on("Expense Claim", {
    cost_center : (frm)=>{
        if(frm.doc.cost_center){
            frm.doc.expenses.forEach(e => {
                frappe.model.set_value(e.doctype, e.name, "cost_center", frm.doc.cost_center)
            });
        }
    },
    project : (frm)=>{
        if(frm.doc.project){
            frm.doc.expenses.forEach(e => {
                frappe.model.set_value(e.doctype, e.name, "project", frm.doc.project)
            });
        }
    }
})
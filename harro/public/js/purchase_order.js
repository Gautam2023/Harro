frappe.ui.form.on("Purchase Order", {
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
    },
    refresh: function (frm) {
        console.log("refresh event got triggered");
        // calling custom function
		if (!frm.doc.custom_company_contact) {
			frappe.call({
				method: "harro.harro.docevents.purchase_order.get_company_contact",
				callback: function (r) {
					if (r.message) {
						console.log(r.message);
						frm.set_value("custom_company_contact",r.message)
					}
				} 
			});
		}
        if (frm.doc.status === "Partially received and To Bill") {
            frm.page.set_indicator(__("Partially received and To Bill"), "orange");
        }
    }
})
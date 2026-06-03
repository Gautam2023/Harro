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


frappe.ui.form.on('Expense Claim Detail', {
    custom_multi_currency: calculate_amount,
    custom_exchange_rate: calculate_amount
});

function calculate_amount(frm, cdt, cdn) {

    console.log("Type:", frm.doc.custom_expense_claim_type);

    if (frm.doc.custom_expense_claim_type !== "Forex Credit Card") {
        console.log("Condition failed");
        return;
    }

    let row = locals[cdt][cdn];

    console.log(row.custom_multi_currency, row.custom_exchange_rate);

    frappe.model.set_value(
        cdt,
        cdn,
        "amount",
        flt(row.custom_multi_currency) * flt(row.custom_exchange_rate)
    );
}